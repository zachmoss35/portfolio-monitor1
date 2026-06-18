"""Read portfolio holdings from CSV."""

from __future__ import annotations

import csv
from pathlib import Path

from portfolio_agent.models import Holding


def load_portfolio(path: Path) -> list[Holding]:
    """Load holdings from CSV.

    Supports the extended schema:
        ticker,shares,cost_basis,company,sector,priority,notes

    And the legacy schema:
        ticker,shares,cost_basis,notes
    """
    holdings: list[Holding] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        has_extended = "company" in fieldnames or "sector" in fieldnames

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
                    company=row.get("company", "").strip() if has_extended else "",
                    sector=row.get("sector", "").strip() if has_extended else "",
                    priority=row.get("priority", "").strip() if has_extended else "",
                )
            )
    return holdings
