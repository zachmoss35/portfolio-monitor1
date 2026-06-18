"""Fetch market data, prices, and valuation metrics via Yahoo Finance."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import yfinance as yf

from portfolio_agent.models import MarketSnapshot, Valuation

logger = logging.getLogger(__name__)


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
        if result != result:  # NaN check
            return None
        return result
    except (TypeError, ValueError):
        return None


def fetch_market_snapshot(ticker: str) -> MarketSnapshot | None:
    """Fetch current market data and valuation for a single ticker."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}
        hist = stock.history(period="2mo")
    except Exception:
        logger.exception("Failed to fetch market data for %s", ticker)
        return None

    if hist.empty:
        logger.warning("No price history for %s", ticker)
        return None

    price = float(hist["Close"].iloc[-1])
    previous_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
    daily_change = price - previous_close
    daily_change_pct = (daily_change / previous_close * 100) if previous_close else 0.0

    change_30d_pct = None
    if len(hist) >= 22:
        price_30d_ago = float(hist["Close"].iloc[-22])
        if price_30d_ago:
            change_30d_pct = (price - price_30d_ago) / price_30d_ago * 100

    volume = int(hist["Volume"].iloc[-1]) if "Volume" in hist else None
    avg_volume = _safe_float(info.get("averageVolume"))
    volume_ratio = None
    if volume and avg_volume and avg_volume > 0:
        volume_ratio = volume / avg_volume

    valuation = Valuation(
        pe_ratio=_safe_float(info.get("trailingPE")),
        forward_pe=_safe_float(info.get("forwardPE")),
        peg_ratio=_safe_float(info.get("pegRatio")),
        price_to_book=_safe_float(info.get("priceToBook")),
        price_to_sales=_safe_float(info.get("priceToSalesTrailing12Months")),
        ev_to_ebitda=_safe_float(info.get("enterpriseToEbitda")),
    )

    return MarketSnapshot(
        ticker=ticker,
        company_name=info.get("shortName") or info.get("longName") or ticker,
        price=price,
        previous_close=previous_close,
        daily_change=daily_change,
        daily_change_pct=daily_change_pct,
        market_cap=_safe_float(info.get("marketCap")),
        volume=volume,
        avg_volume=int(avg_volume) if avg_volume else None,
        volume_ratio=volume_ratio,
        change_30d_pct=change_30d_pct,
        valuation=valuation,
        sector=info.get("sector", ""),
        industry=info.get("industry", ""),
    )


def fetch_all_snapshots(tickers: list[str]) -> dict[str, MarketSnapshot]:
    """Fetch market snapshots for multiple tickers."""
    results: dict[str, MarketSnapshot] = {}
    for ticker in tickers:
        snapshot = fetch_market_snapshot(ticker)
        if snapshot:
            results[ticker] = snapshot
    return results
