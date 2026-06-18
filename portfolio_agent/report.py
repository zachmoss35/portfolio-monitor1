"""Generate daily Markdown portfolio reports."""

from __future__ import annotations

from datetime import date
from pathlib import Path

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


def _flag_emoji(flag: Flag) -> str:
    return {Flag.BUY: "🟢 BUY", Flag.WATCH: "🟡 WATCH", Flag.SELL: "🔴 SELL", Flag.HOLD: "⚪ HOLD"}[flag]


def generate_report(report: DailyReport) -> str:
    """Render a DailyReport as a Markdown string."""
    lines: list[str] = []
    d = report.report_date

    lines.append(f"# Portfolio Daily Report — {d.strftime('%A, %B %d, %Y')}")
    lines.append("")
    lines.append("## Portfolio Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Value | {_fmt_money(report.portfolio_value)} |")
    lines.append(f"| Total Cost | {_fmt_money(report.portfolio_cost)} |")
    lines.append(f"| P&L | {_fmt_money(report.portfolio_pnl)} ({_fmt_pct(report.portfolio_pnl_pct)}) |")
    lines.append(f"| Holdings | {len(report.analyses)} |")
    lines.append("")

    # Flags summary
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

    # Per-ticker updates
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
        lines.append(f"| | |")
        lines.append(f"|---|---|")
        lines.append(f"| Price | {_fmt_money(m.price)} ({_fmt_pct(m.daily_change_pct)} today) |")
        lines.append(f"| Position | {h.shares:.0f} shares @ {_fmt_money(h.cost_basis)} |")
        lines.append(f"| Position Value | {_fmt_money(position_value)} |")
        lines.append(f"| Position P&L | {_fmt_money(position_pnl)} ({_fmt_pct(position_pnl_pct)}) |")
        lines.append(f"| Market Cap | {_fmt_money(m.market_cap)} |")
        lines.append(f"| Volume | {m.volume:,}" if m.volume else "| Volume | N/A |")
        if m.volume_ratio:
            lines.append(f"| Vol / Avg | {m.volume_ratio:.1f}x |")
        lines.append(f"| 30d Change | {_fmt_pct(m.change_30d_pct)} |")
        if h.notes:
            lines.append(f"| Notes | {h.notes} |")
        lines.append("")

    # Valuation changes
    lines.append("## Valuation Metrics")
    lines.append("")
    lines.append("| Ticker | P/E | Fwd P/E | PEG | P/B | P/S | EV/EBITDA |")
    lines.append("|--------|-----|---------|-----|-----|-----|-----------|")
    for a in report.analyses:
        v = a.market.valuation
        lines.append(
            f"| {a.holding.ticker} "
            f"| {v.pe_ratio or '—'} "
            f"| {v.forward_pe or '—'} "
            f"| {v.peg_ratio or '—'} "
            f"| {v.price_to_book or '—'} "
            f"| {v.price_to_sales or '—'} "
            f"| {v.ev_to_ebitda or '—'} |"
        )
    lines.append("")

    # Earnings calendar
    lines.append("## Earnings Calendar")
    lines.append("")
    upcoming = [a for a in report.analyses if a.earnings.earnings_date]
    if upcoming:
        lines.append("| Ticker | Next Earnings | Days Away |")
        lines.append("|--------|---------------|-----------|")
        for a in sorted(upcoming, key=lambda x: x.earnings.days_to_earnings or 999):
            e = a.earnings
            lines.append(
                f"| {a.holding.ticker} "
                f"| {e.earnings_date} "
                f"| {e.days_to_earnings} |"
            )
    else:
        lines.append("_No upcoming earnings dates found._")
    lines.append("")

    # New filings
    lines.append("## New SEC Filings")
    lines.append("")
    has_filings = False
    for a in report.analyses:
        new_filings = [f for f in a.filings if f.is_new]
        if new_filings:
            has_filings = True
            lines.append(f"### {a.holding.ticker}")
            for f in new_filings:
                lines.append(f"- **{f.form_type}** ({f.filed_date}): {f.description} — [View]({f.link})")
            lines.append("")
    if not has_filings:
        all_recent = [(a.holding.ticker, f) for a in report.analyses for f in a.filings[:3]]
        if all_recent:
            lines.append("_No new filings today. Recent filings:_")
            lines.append("")
            for ticker, f in all_recent:
                lines.append(f"- **{ticker}** {f.form_type} ({f.filed_date}): [View]({f.link})")
        else:
            lines.append("_No recent filings found._")
    lines.append("")

    # Material news
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
        lines.append("_No material news detected. Recent headlines:_")
        lines.append("")
        for a in report.analyses:
            for n in a.news[:2]:
                pub = n.published.strftime("%Y-%m-%d") if n.published else "—"
                link = f" — [Read]({n.link})" if n.link else ""
                lines.append(f"- **{a.holding.ticker}** | {pub}: {n.title}{link}")
    lines.append("")

    # Screener results
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
