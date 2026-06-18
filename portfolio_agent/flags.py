"""Determine buy/watch/sell flags from screener hits and market data."""

from __future__ import annotations

from portfolio_agent.models import Flag, ScreenerHit, TickerAnalysis

SEVERITY_RANK = {Flag.SELL: 0, Flag.WATCH: 1, Flag.HOLD: 2, Flag.BUY: 3}


def determine_flag(hits: list[ScreenerHit]) -> Flag:
    """Pick the most actionable flag from screener hits."""
    if not hits:
        return Flag.HOLD

    flags = [h.severity for h in hits]
    if Flag.SELL in flags:
        return Flag.SELL
    if Flag.BUY in flags and Flag.WATCH not in flags:
        return Flag.BUY
    if Flag.BUY in flags:
        return Flag.WATCH
    if Flag.WATCH in flags:
        return Flag.WATCH
    return Flag.HOLD


def apply_flags(analyses: list[TickerAnalysis]) -> list[TickerAnalysis]:
    """Set the flag field on each analysis based on screener hits."""
    for analysis in analyses:
        analysis.flag = determine_flag(analysis.screener_hits)
    return analyses
