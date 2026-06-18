"""Tests for portfolio CSV loading."""

from pathlib import Path

from portfolio_agent.portfolio import load_portfolio


def test_load_portfolio(tmp_path: Path):
    csv = tmp_path / "portfolio.csv"
    csv.write_text("ticker,shares,cost_basis,notes\nAAPL,10,150.00,Test\n")
    holdings = load_portfolio(csv)
    assert len(holdings) == 1
    assert holdings[0].ticker == "AAPL"
    assert holdings[0].shares == 10
    assert holdings[0].cost_basis == 150.0
    assert holdings[0].notes == "Test"


def test_load_portfolio_uppercases_ticker(tmp_path: Path):
    csv = tmp_path / "portfolio.csv"
    csv.write_text("ticker,shares,cost_basis,notes\naapl,5,100,\n")
    holdings = load_portfolio(csv)
    assert holdings[0].ticker == "AAPL"


def test_load_portfolio_extended_schema(tmp_path: Path):
    csv = tmp_path / "portfolio.csv"
    csv.write_text(
        "ticker,shares,cost_basis,company,sector,priority,notes\n"
        "AAPL,50,175.00,Apple Inc.,Technology,high,Core holding\n"
    )
    holdings = load_portfolio(csv)
    assert len(holdings) == 1
    h = holdings[0]
    assert h.ticker == "AAPL"
    assert h.company == "Apple Inc."
    assert h.sector == "Technology"
    assert h.priority == "high"
    assert h.notes == "Core holding"


def test_load_portfolio_legacy_schema_ignores_extended_fields(tmp_path: Path):
    csv = tmp_path / "portfolio.csv"
    csv.write_text("ticker,shares,cost_basis,notes\nMSFT,30,380.00,Cloud\n")
    holdings = load_portfolio(csv)
    h = holdings[0]
    assert h.company == ""
    assert h.sector == ""
    assert h.notes == "Cloud"
