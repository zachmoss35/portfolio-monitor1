"""Valuation flag detection."""

from __future__ import annotations

from portfolio_agent.models import Valuation, ValuationFlag


def compute_valuation_flags(
    valuation: Valuation,
    prior_valuation: Valuation | None = None,
) -> list[ValuationFlag]:
    """Detect valuation signals from current and prior metrics."""
    flags: list[ValuationFlag] = []

    pe = valuation.pe_ratio
    fwd_pe = valuation.forward_pe
    peg = valuation.peg_ratio
    pb = valuation.price_to_book
    ps = valuation.price_to_sales

    has_data = any(v is not None for v in [pe, fwd_pe, peg, pb, ps, valuation.ev_to_ebitda])
    if not has_data:
        flags.append(ValuationFlag.MISSING_DATA)
        return flags

    # Expensive growth: high P/E or PEG
    if (pe is not None and pe > 40) or (peg is not None and peg > 2.5):
        flags.append(ValuationFlag.EXPENSIVE_GROWTH)
    elif fwd_pe is not None and pe is not None and fwd_pe > pe * 1.1:
        flags.append(ValuationFlag.EXPENSIVE_GROWTH)

    # Cheap value: low P/E and P/B
    if (pe is not None and pe < 15) and (pb is not None and pb < 2):
        flags.append(ValuationFlag.CHEAP_VALUE)
    elif pe is not None and pe < 12:
        flags.append(ValuationFlag.CHEAP_VALUE)

    if prior_valuation:
        _check_multiple_change(valuation, prior_valuation, flags)

    return flags


def _check_multiple_change(
    current: Valuation,
    prior: Valuation,
    flags: list[ValuationFlag],
) -> None:
    """Detect multiple expansion or compression vs prior snapshot."""
    pairs = [
        (current.pe_ratio, prior.pe_ratio),
        (current.forward_pe, prior.forward_pe),
        (current.ev_to_ebitda, prior.ev_to_ebitda),
        (current.price_to_sales, prior.price_to_sales),
    ]
    expansions = 0
    compressions = 0
    for cur, prev in pairs:
        if cur is None or prev is None or prev == 0:
            continue
        change = (cur - prev) / abs(prev)
        if change > 0.05:
            expansions += 1
        elif change < -0.05:
            compressions += 1

    if expansions >= 2:
        flags.append(ValuationFlag.MULTIPLE_EXPANSION)
    if compressions >= 2:
        flags.append(ValuationFlag.MULTIPLE_COMPRESSION)


def format_valuation_flag(flag: ValuationFlag) -> str:
    labels = {
        ValuationFlag.EXPENSIVE_GROWTH: "Expensive growth",
        ValuationFlag.CHEAP_VALUE: "Cheap value",
        ValuationFlag.MULTIPLE_EXPANSION: "Multiple expansion",
        ValuationFlag.MULTIPLE_COMPRESSION: "Multiple compression",
        ValuationFlag.MISSING_DATA: "Missing data",
    }
    return labels.get(flag, flag.value)
