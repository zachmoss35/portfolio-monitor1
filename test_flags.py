"""Tests for buy/watch/sell flag logic."""

from portfolio_agent.flags import determine_flag
from portfolio_agent.models import Flag, ScreenerHit


def _hit(severity: str) -> ScreenerHit:
    return ScreenerHit(
        ticker="X",
        rule_name="test",
        description="test",
        severity=Flag(severity),
        field="x",
        actual_value=1,
    )


def test_no_hits_is_hold():
    assert determine_flag([]) == Flag.HOLD


def test_sell_takes_priority():
    hits = [_hit("buy"), _hit("sell")]
    assert determine_flag(hits) == Flag.SELL


def test_buy_and_watch_becomes_watch():
    hits = [_hit("buy"), _hit("watch")]
    assert determine_flag(hits) == Flag.WATCH


def test_buy_only():
    hits = [_hit("buy")]
    assert determine_flag(hits) == Flag.BUY
