"""Tests for screener rule evaluation."""

from portfolio_agent.models import EarningsEvent, Flag, MarketSnapshot, Valuation
from portfolio_agent.screener import evaluate_rule, run_screeners


def _market(**kwargs) -> MarketSnapshot:
    defaults = dict(
        ticker="TEST",
        company_name="Test Co",
        price=100.0,
        previous_close=98.0,
        daily_change=2.0,
        daily_change_pct=2.04,
        market_cap=1e9,
        volume=1_000_000,
        avg_volume=500_000,
        volume_ratio=2.0,
        change_30d_pct=5.0,
        valuation=Valuation(pe_ratio=25.0),
    )
    defaults.update(kwargs)
    return MarketSnapshot(**defaults)


def _earnings(**kwargs) -> EarningsEvent:
    defaults = dict(ticker="TEST", earnings_date=None, days_to_earnings=5)
    defaults.update(kwargs)
    return EarningsEvent(**defaults)


def test_daily_drop_triggers():
    rule = {
        "name": "daily_drop",
        "field": "daily_change_pct",
        "operator": "lt",
        "value": -3.0,
        "severity": "watch",
        "description": "Big drop",
    }
    hit = evaluate_rule(rule, _market(daily_change_pct=-5.0), _earnings())
    assert hit is not None
    assert hit.severity == Flag.WATCH


def test_daily_drop_no_trigger():
    rule = {
        "name": "daily_drop",
        "field": "daily_change_pct",
        "operator": "lt",
        "value": -3.0,
        "severity": "watch",
        "description": "Big drop",
    }
    hit = evaluate_rule(rule, _market(daily_change_pct=1.0), _earnings())
    assert hit is None


def test_between_operator():
    rule = {
        "name": "earnings_soon",
        "field": "days_to_earnings",
        "operator": "between",
        "value": [0, 7],
        "severity": "watch",
        "description": "Earnings this week",
    }
    hit = evaluate_rule(rule, _market(), _earnings(days_to_earnings=3))
    assert hit is not None


def test_run_screeners_multiple():
    rules = [
        {
            "name": "vol_spike",
            "field": "volume_ratio",
            "operator": "gt",
            "value": 1.5,
            "severity": "watch",
            "description": "Volume spike",
        },
        {
            "name": "high_pe",
            "field": "pe_ratio",
            "operator": "gt",
            "value": 50,
            "severity": "sell",
            "description": "Expensive",
        },
    ]
    hits = run_screeners(rules, _market(), _earnings())
    assert len(hits) == 1
    assert hits[0].rule_name == "vol_spike"
