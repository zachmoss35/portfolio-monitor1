"""Evaluate screener rules from YAML against ticker data."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from portfolio_agent.models import (
    EarningsEvent,
    Flag,
    MarketSnapshot,
    ScreenerHit,
)

logger = logging.getLogger(__name__)

OPERATORS = {
    "gt": lambda a, b: a is not None and a > b,
    "gte": lambda a, b: a is not None and a >= b,
    "lt": lambda a, b: a is not None and a < b,
    "lte": lambda a, b: a is not None and a <= b,
    "eq": lambda a, b: a is not None and a == b,
    "between": lambda a, b: a is not None and b[0] <= a <= b[1],
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}


def load_rules(path: Path) -> list[dict[str, Any]]:
    """Load screener rules from YAML."""
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("rules", [])


def _resolve_field(
    field: str, market: MarketSnapshot, earnings: EarningsEvent
) -> float | str | None:
    """Map a rule field name to its value from market/earnings data."""
    field_map: dict[str, Any] = {
        "daily_change_pct": market.daily_change_pct,
        "daily_change": market.daily_change,
        "price": market.price,
        "market_cap": market.market_cap,
        "volume": market.volume,
        "volume_ratio": market.volume_ratio,
        "change_30d_pct": market.change_30d_pct,
        "pe_ratio": market.valuation.pe_ratio,
        "forward_pe": market.valuation.forward_pe,
        "peg_ratio": market.valuation.peg_ratio,
        "price_to_book": market.valuation.price_to_book,
        "price_to_sales": market.valuation.price_to_sales,
        "ev_to_ebitda": market.valuation.ev_to_ebitda,
        "days_to_earnings": earnings.days_to_earnings,
        "sector": market.sector,
        "industry": market.industry,
    }
    return field_map.get(field)


def evaluate_rule(
    rule: dict[str, Any],
    market: MarketSnapshot,
    earnings: EarningsEvent,
) -> ScreenerHit | None:
    """Evaluate a single screener rule. Returns a hit if the rule matches."""
    field = rule["field"]
    operator = rule["operator"]
    expected = rule["value"]
    actual = _resolve_field(field, market, earnings)

    if actual is None:
        return None

    op_fn = OPERATORS.get(operator)
    if not op_fn:
        logger.warning("Unknown operator: %s", operator)
        return None

    try:
        if not op_fn(actual, expected):
            return None
    except (TypeError, ValueError):
        return None

    severity_str = rule.get("severity", "watch")
    severity = Flag(severity_str) if severity_str in Flag._value2member_map_ else Flag.WATCH

    return ScreenerHit(
        ticker=market.ticker,
        rule_name=rule["name"],
        description=rule.get("description", rule["name"]),
        severity=severity,
        field=field,
        actual_value=actual,
    )


def run_screeners(
    rules: list[dict[str, Any]],
    market: MarketSnapshot,
    earnings: EarningsEvent,
) -> list[ScreenerHit]:
    """Run all screener rules against a ticker's data."""
    hits: list[ScreenerHit] = []
    for rule in rules:
        hit = evaluate_rule(rule, market, earnings)
        if hit:
            hits.append(hit)
    return hits
