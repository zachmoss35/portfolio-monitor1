"""Save and load report snapshots for day-over-day comparison."""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

from portfolio_agent.models import DailyReport, TickerAnalysis, Valuation

logger = logging.getLogger(__name__)


def _valuation_to_dict(v: Valuation) -> dict:
    return {
        "pe_ratio": v.pe_ratio,
        "forward_pe": v.forward_pe,
        "peg_ratio": v.peg_ratio,
        "price_to_book": v.price_to_book,
        "price_to_sales": v.price_to_sales,
        "ev_to_ebitda": v.ev_to_ebitda,
        "ev_to_sales": v.ev_to_sales,
        "fcf_yield": v.fcf_yield,
        "dividend_yield": v.dividend_yield,
    }


def _analysis_to_dict(a: TickerAnalysis) -> dict:
    return {
        "ticker": a.holding.ticker,
        "price": a.market.price,
        "daily_change_pct": a.market.daily_change_pct,
        "valuation": _valuation_to_dict(a.market.valuation),
        "filing_ids": [f"{f.form_type}:{f.filed_date.isoformat()}" for f in a.filings],
        "news_titles": [n.title for n in a.news],
        "earnings_date": a.earnings.earnings_date.isoformat() if a.earnings.earnings_date else None,
        "days_to_earnings": a.earnings.days_to_earnings,
    }


def save_snapshot(report: DailyReport, snapshots_dir: Path) -> Path:
    """Save a JSON snapshot of today's report data."""
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    path = snapshots_dir / f"{report.report_date.isoformat()}.json"
    payload = {
        "report_date": report.report_date.isoformat(),
        "portfolio_value": report.portfolio_value,
        "tickers": [_analysis_to_dict(a) for a in report.analyses],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_prior_snapshot(snapshots_dir: Path, before_date: date) -> dict | None:
    """Load the most recent snapshot before the given date."""
    if not snapshots_dir.is_dir():
        return None
    candidates = sorted(
        snapshots_dir.glob("*.json"),
        key=lambda p: p.stem,
        reverse=True,
    )
    for path in candidates:
        try:
            snap_date = date.fromisoformat(path.stem)
        except ValueError:
            continue
        if snap_date < before_date:
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                logger.warning("Failed to read snapshot %s", path)
    return None


def prior_valuation_for_ticker(prior: dict | None, ticker: str) -> Valuation | None:
    """Extract prior valuation for a ticker from a snapshot."""
    if not prior:
        return None
    for entry in prior.get("tickers", []):
        if entry.get("ticker") == ticker:
            v = entry.get("valuation", {})
            return Valuation(**{k: v.get(k) for k in _valuation_to_dict(Valuation())})
    return None
