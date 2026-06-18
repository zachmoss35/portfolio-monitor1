"""Day-over-day change detection."""

from __future__ import annotations

from portfolio_agent.models import DailyChanges, DailyReport, TickerChange


def _fmt_val_change(label: str, cur: float | None, prev: float | None) -> str | None:
    if cur is None or prev is None or prev == 0:
        return None
    change = (cur - prev) / abs(prev) * 100
    if abs(change) < 1:
        return None
    direction = "up" if change > 0 else "down"
    return f"{label} {direction} {abs(change):.1f}% ({prev:.1f} → {cur:.1f})"


def compute_daily_changes(
    report: DailyReport,
    prior: dict | None,
) -> DailyChanges:
    """Compare today's report to the prior snapshot."""
    changes = DailyChanges()
    if not prior:
        return changes

    changes.has_prior = True
    changes.prior_date = prior.get("report_date", "")

    prior_by_ticker = {t["ticker"]: t for t in prior.get("tickers", [])}

    for a in report.analyses:
        ticker = a.holding.ticker
        prev = prior_by_ticker.get(ticker)
        if not prev:
            continue

        tc = TickerChange(ticker=ticker)

        prev_pct = prev.get("daily_change_pct")
        cur_pct = a.market.daily_change_pct
        if prev_pct is not None:
            tc.price_change_pct = cur_pct - prev_pct

        prev_filings = set(prev.get("filing_ids", []))
        cur_filings = {f"{f.form_type}:{f.filed_date.isoformat()}" for f in a.filings}
        tc.new_filings = sorted(cur_filings - prev_filings)

        prev_news = set(prev.get("news_titles", []))
        tc.new_news = [n.title for n in a.news if n.title not in prev_news]

        prev_earn = prev.get("earnings_date")
        cur_earn = a.earnings.earnings_date.isoformat() if a.earnings.earnings_date else None
        if cur_earn != prev_earn:
            if cur_earn:
                tc.earnings_update = f"Earnings date updated to {cur_earn}"
            elif prev_earn:
                tc.earnings_update = f"Earnings date removed (was {prev_earn})"

        prev_val = prev.get("valuation", {})
        cur_val = a.market.valuation
        val_changes = []
        for label, attr in [
            ("P/E", "pe_ratio"),
            ("Fwd P/E", "forward_pe"),
            ("EV/EBITDA", "ev_to_ebitda"),
            ("P/S", "price_to_sales"),
        ]:
            msg = _fmt_val_change(label, getattr(cur_val, attr), prev_val.get(attr))
            if msg:
                val_changes.append(msg)
        tc.valuation_changes = val_changes

        if any([tc.new_filings, tc.new_news, tc.earnings_update, tc.valuation_changes,
                tc.price_change_pct is not None and abs(tc.price_change_pct) >= 0.5]):
            changes.ticker_changes.append(tc)

    return changes
