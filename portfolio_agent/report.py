"""Generate daily Markdown portfolio reports."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from portfolio_agent.analysis.valuation_flags import format_valuation_flag
from portfolio_agent.config import Config
from portfolio_agent.models import DailyReport, Flag, TickerAnalysis


def _fmt_money(value: float | None) -> str:
    if value is None:
        return "N/A"
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,.2f}"


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


def _fmt_ratio(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.2f}"


def _flag_emoji(flag: Flag) -> str:
    return {Flag.BUY: "🟢 BUY", Flag.WATCH: "🟡 WATCH", Flag.SELL: "🔴 SELL", Flag.HOLD: "⚪ HOLD"}[flag]


def _render_executive_summary(report: DailyReport) -> list[str]:
    lines: list[str] = []
    es = report.executive_summary
    lines.append("## Executive Summary")
    lines.append("")

    lines.append("### Top Positive Developments")
    if es.top_positive:
        for item in es.top_positive:
            lines.append(f"- {item}")
    else:
        lines.append("_None above threshold._")
    lines.append("")

    lines.append("### Top Negative Developments")
    if es.top_negative:
        for item in es.top_negative:
            lines.append(f"- {item}")
    else:
        lines.append("_None above threshold._")
    lines.append("")

    lines.append("### Companies Requiring Review")
    if es.needs_review:
        for item in es.needs_review:
            lines.append(f"- {item}")
    else:
        lines.append("_No companies flagged for review._")
    lines.append("")

    lines.append("### Upcoming Earnings (30 days)")
    if es.upcoming_earnings:
        for item in es.upcoming_earnings:
            lines.append(f"- {item}")
    else:
        lines.append("_No earnings within 30 days._")
    lines.append("")

    lines.append("### Major Price Movers")
    if es.major_movers:
        for item in es.major_movers:
            lines.append(f"- {item}")
    else:
        lines.append("_No major movers today._")
    lines.append("")

    return lines


def _render_daily_changes(report: DailyReport) -> list[str]:
    lines: list[str] = []
    dc = report.daily_changes
    lines.append("## What Changed Since Yesterday?")
    lines.append("")

    if not dc.has_prior:
        lines.append("_No prior report snapshot available. Changes will appear starting tomorrow._")
        lines.append("")
        return lines

    lines.append(f"_Compared to snapshot from {dc.prior_date}._")
    lines.append("")

    if not dc.ticker_changes:
        lines.append("_No material changes detected._")
        lines.append("")
        return lines

    for tc in dc.ticker_changes:
        lines.append(f"### {tc.ticker}")
        if tc.price_change_pct is not None:
            lines.append(f"- Price momentum shift: {tc.price_change_pct:+.1f}pp vs prior day")
        for title in tc.new_news:
            lines.append(f"- New news: {title}")
        for filing in tc.new_filings:
            lines.append(f"- New filing: {filing}")
        if tc.earnings_update:
            lines.append(f"- {tc.earnings_update}")
        for vc in tc.valuation_changes:
            lines.append(f"- Valuation: {vc}")
        lines.append("")

    return lines


def _render_ticker_extras(a: TickerAnalysis) -> list[str]:
    lines: list[str] = []
    if a.valuation_flags:
        flags = ", ".join(format_valuation_flag(f) for f in a.valuation_flags)
        lines.append(f"**Valuation Flags:** {flags}")
    if a.ai_summary:
        s = a.ai_summary
        lines.append("")
        lines.append("**AI Analyst Notes:**")
        if s.what_changed:
            lines.append(f"- What changed? {s.what_changed}")
        if s.why_it_matters:
            lines.append(f"- Why it matters? {s.why_it_matters}")
        if s.action_item:
            lines.append(f"- Action item: {s.action_item}")
    lines.append("")
    return lines


def generate_report(report: DailyReport, config: Config | None = None) -> str:
    """Render a DailyReport as a Markdown string."""
    lines: list[str] = []
    d = report.report_date

    lines.append(f"# Portfolio Daily Report — {d.strftime('%A, %B %d, %Y')}")
    lines.append("")
    lines.extend(_render_executive_summary(report))
    lines.extend(_render_daily_changes(report))

    lines.append("## Portfolio Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Value | {_fmt_money(report.portfolio_value)} |")
    lines.append(f"| Total Cost | {_fmt_money(report.portfolio_cost)} |")
    lines.append(f"| P&L | {_fmt_money(report.portfolio_pnl)} ({_fmt_pct(report.portfolio_pnl_pct)}) |")
    lines.append(f"| Holdings | {len(report.analyses)} |")
    lines.append("")

    lines.append("## Action Flags")
    lines.append("")
    for flag in (Flag.BUY, Flag.WATCH, Flag.SELL):
        tickers = [a.holding.ticker for a in report.analyses if a.flag == flag]
        if tickers:
            lines.append(f"**{_flag_emoji(flag)}**: {', '.join(tickers)}")
    hold_tickers = [a.holding.ticker for a in report.analyses if a.flag == Flag.HOLD]
    if hold_tickers:
        lines.append(f"**{_flag_emoji(Flag.HOLD)}**: {', '.join(hold_tickers)}")
    lines.append("")

    lines.append("## Portfolio Company Updates")
    lines.append("")
    for a in report.analyses:
        m = a.market
        h = a.holding
        position_value = m.price * h.shares
        position_pnl = (m.price - h.cost_basis) * h.shares
        position_pnl_pct = ((m.price - h.cost_basis) / h.cost_basis * 100) if h.cost_basis else 0

        lines.append(f"### {m.ticker} — {m.company_name} {_flag_emoji(a.flag)}")
        lines.append("")
        lines.append("| | |")
        lines.append("|---|---|")
        lines.append(f"| Price | {_fmt_money(m.price)} ({_fmt_pct(m.daily_change_pct)} today) |")
        lines.append(f"| Position | {h.shares:.0f} shares @ {_fmt_money(h.cost_basis)} |")
        lines.append(f"| Position Value | {_fmt_money(position_value)} |")
        lines.append(f"| Position P&L | {_fmt_money(position_pnl)} ({_fmt_pct(position_pnl_pct)}) |")
        lines.append(f"| Market Cap | {_fmt_money(m.market_cap)} |")
        lines.append(f"| Volume | {m.volume:,}" if m.volume else "| Volume | N/A |")
        if m.volume_ratio:
            lines.append(f"| Vol / Avg | {m.volume_ratio:.1f}x |")
        lines.append(f"| 30d Change | {_fmt_pct(m.change_30d_pct)} |")
        if h.sector or m.sector:
            lines.append(f"| Sector | {h.sector or m.sector} |")
        if h.priority:
            lines.append(f"| Priority | {h.priority} |")
        if h.notes:
            lines.append(f"| Notes | {h.notes} |")
        lines.append("")
        lines.extend(_render_ticker_extras(a))

    lines.append("## Valuation Metrics")
    lines.append("")
    lines.append(
        "| Ticker | P/E | Fwd P/E | EV/Sales | EV/EBITDA | P/S | FCF Yield | Div Yield | Flags |"
    )
    lines.append("|--------|-----|---------|----------|-----------|-----|-----------|-----------|-------|")
    for a in report.analyses:
        v = a.market.valuation
        flags = ", ".join(format_valuation_flag(f) for f in a.valuation_flags) or "—"
        lines.append(
            f"| {a.holding.ticker} "
            f"| {_fmt_ratio(v.pe_ratio)} "
            f"| {_fmt_ratio(v.forward_pe)} "
            f"| {_fmt_ratio(v.ev_to_sales)} "
            f"| {_fmt_ratio(v.ev_to_ebitda)} "
            f"| {_fmt_ratio(v.price_to_sales)} "
            f"| {_fmt_ratio(v.fcf_yield)}{'%' if v.fcf_yield else ''} "
            f"| {_fmt_ratio(v.dividend_yield)}{'%' if v.dividend_yield else ''} "
            f"| {flags} |"
        )
    lines.append("")

    lines.append("## Earnings Calendar")
    lines.append("")
    upcoming = [a for a in report.analyses if a.earnings.earnings_date]
    if upcoming:
        lines.append("| Ticker | Next Earnings | Days Away | Last Earnings | Flags |")
        lines.append("|--------|---------------|-----------|---------------|-------|")
        for a in sorted(upcoming, key=lambda x: x.earnings.days_to_earnings or 999):
            e = a.earnings
            flags = []
            if e.within_14_days:
                flags.append("⚠️ 14d")
            if e.within_30_days:
                flags.append("30d")
            flag_str = ", ".join(flags) if flags else "—"
            last = e.last_earnings_date or "—"
            lines.append(
                f"| {a.holding.ticker} "
                f"| {e.earnings_date} "
                f"| {e.days_to_earnings} "
                f"| {last} "
                f"| {flag_str} |"
            )
    else:
        lines.append("_No upcoming earnings dates found._")
    lines.append("")

    lines.append("## SEC Filings")
    lines.append("")
    has_filings = False
    for a in report.analyses:
        ticker_filings = sorted(
            a.filings,
            key=lambda f: (not f.is_high_priority, not f.is_new, f.filed_date),
            reverse=True,
        )
        display = [f for f in ticker_filings if f.is_new or f.is_high_priority][:5]
        if not display:
            display = ticker_filings[:3]
        if display:
            has_filings = True
            lines.append(f"### {a.holding.ticker}")
            for f in display:
                priority = " 🔴" if f.is_high_priority else ""
                new_tag = " **NEW**" if f.is_new else ""
                lines.append(
                    f"- **{f.category}**{priority}{new_tag} ({f.filed_date}): "
                    f"{f.relevance_summary} — [View]({f.link})"
                )
            lines.append("")
    if not has_filings:
        lines.append("_No recent filings found._")
    lines.append("")

    lines.append("## Material News")
    lines.append("")
    has_news = False
    for a in report.analyses:
        material = [n for n in a.news if n.is_material]
        if material:
            has_news = True
            lines.append(f"### {a.holding.ticker}")
            for n in material:
                pub = n.published.strftime("%Y-%m-%d") if n.published else "—"
                link = f" — [Read]({n.link})" if n.link else ""
                lines.append(f"- **{pub}** | {n.publisher}: {n.title}{link}")
            lines.append("")
    if not has_news:
        lines.append("_No material news detected. Recent relevant headlines:_")
        lines.append("")
        for a in report.analyses:
            for n in a.news[:2]:
                pub = n.published.strftime("%Y-%m-%d") if n.published else "—"
                link = f" — [Read]({n.link})" if n.link else ""
                lines.append(f"- **{a.holding.ticker}** | {pub}: {n.title}{link}")
    lines.append("")

    lines.append("## Screener Results")
    lines.append("")
    has_hits = False
    for a in report.analyses:
        if a.screener_hits:
            has_hits = True
            lines.append(f"### {a.holding.ticker}")
            for hit in a.screener_hits:
                lines.append(
                    f"- **{hit.rule_name}** ({_flag_emoji(hit.severity)}): "
                    f"{hit.description} — `{hit.field}` = {hit.actual_value}"
                )
            lines.append("")
    if not has_hits:
        lines.append("_No screener rules triggered._")
    lines.append("")

    lines.append("---")
    lines.append(f"_Generated by Portfolio Monitor on {d.isoformat()}_")
    return "\n".join(lines)


def save_report(content: str, reports_dir: Path, report_date: date | None = None) -> Path:
    """Save report Markdown to reports/YYYY-MM-DD.md."""
    report_date = report_date or date.today()
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"{report_date.isoformat()}.md"
    path.write_text(content, encoding="utf-8")
    return path
