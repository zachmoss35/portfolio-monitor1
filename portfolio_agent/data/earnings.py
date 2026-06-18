"""Fetch earnings calendar data."""

from __future__ import annotations

import logging
from datetime import date, datetime

import yfinance as yf

from portfolio_agent.models import EarningsEvent

logger = logging.getLogger(__name__)


def fetch_earnings(ticker: str) -> EarningsEvent:
    """Fetch next earnings date and estimates for a ticker."""
    try:
        stock = yf.Ticker(ticker)
        cal = stock.calendar
        info = stock.info or {}
    except Exception:
        logger.exception("Failed to fetch earnings for %s", ticker)
        return EarningsEvent(ticker=ticker, earnings_date=None, days_to_earnings=None)

    earnings_date = None
    days_to_earnings = None

    if cal is not None and not (hasattr(cal, "empty") and cal.empty):
        if isinstance(cal, dict):
            raw_date = cal.get("Earnings Date")
            if isinstance(raw_date, list) and raw_date:
                raw_date = raw_date[0]
            if raw_date:
                earnings_date = _parse_date(raw_date)
        elif hasattr(cal, "index"):
            for idx in cal.index:
                if "earnings" in str(idx).lower():
                    val = cal.loc[idx]
                    if hasattr(val, "iloc"):
                        val = val.iloc[0]
                    earnings_date = _parse_date(val)
                    break

    if earnings_date:
        days_to_earnings = (earnings_date - date.today()).days

    return EarningsEvent(
        ticker=ticker,
        earnings_date=earnings_date,
        days_to_earnings=days_to_earnings,
        eps_estimate=_safe_float(info.get("epsForward") or info.get("forwardEps")),
        revenue_estimate=_safe_float(info.get("totalRevenue")),
    )


def _parse_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except (ValueError, TypeError):
        return None


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
        return None if result != result else result
    except (TypeError, ValueError):
        return None
