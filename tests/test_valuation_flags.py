"""Tests for valuation flag detection."""

from portfolio_agent.analysis.valuation_flags import compute_valuation_flags
from portfolio_agent.models import Valuation, ValuationFlag


def test_missing_data_flag():
    flags = compute_valuation_flags(Valuation())
    assert ValuationFlag.MISSING_DATA in flags


def test_expensive_growth_flag():
    flags = compute_valuation_flags(Valuation(pe_ratio=50.0, peg_ratio=3.0))
    assert ValuationFlag.EXPENSIVE_GROWTH in flags


def test_cheap_value_flag():
    flags = compute_valuation_flags(Valuation(pe_ratio=10.0, price_to_book=1.5))
    assert ValuationFlag.CHEAP_VALUE in flags


def test_multiple_expansion():
    current = Valuation(pe_ratio=30.0, forward_pe=25.0, ev_to_ebitda=15.0)
    prior = Valuation(pe_ratio=25.0, forward_pe=20.0, ev_to_ebitda=12.0)
    flags = compute_valuation_flags(current, prior)
    assert ValuationFlag.MULTIPLE_EXPANSION in flags
