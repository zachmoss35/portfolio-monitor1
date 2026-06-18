"""Read portfolio holdings from CSV."""

from __future__ import annotations

import csv
from pathlib import Path

from portfolio_agent.models import Holding


def load_portfolio(path: Path) -> list[Holding]:
    """Load holdings from a CSV with columns: ticker, shares, cost_basis, notes."""
    holdings: list[Holding] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticker = row["ticker"].strip().upper()
            if not ticker:
                continue
            holdings.append(
                Holding(
                    ticker=ticker,
                    shares=float(row["shares"]),
                    cost_basis=float(row["cost_basis"]),
                    notes=row.get("notes", "").strip(),
                )
            )
    return holdings
