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
