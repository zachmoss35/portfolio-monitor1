"""Tests for day-over-day change detection."""

from datetime import date

from portfolio_agent.analysis.changes import compute_daily_changes
from portfolio_agent.models import (
    DailyReport,
    EarningsEvent,
    Holding,
    MarketSnapshot,
    NewsItem,
    SECFiling,
    TickerAnalysis,
    Valuation,
)


def _report() -> DailyReport:
    return DailyReport(
        report_date=date(2026, 6, 18),
        analyses=[
            TickerAnalysis(
                holding=Holding(ticker="AAPL", shares=10, cost_basis=100.0),
                market=MarketSnapshot(
                    ticker="AAPL",
                    company_name="Apple",
                    price=155.0,
                    previous_close=150.0,
                    daily_change=5.0,
                    daily_change_pct=3.33,
                    market_cap=1e12,
                    volume=1e7,
                    avg_volume=1e7,
                    volume_ratio=1.0,
                    change_30d_pct=5.0,
                    valuation=Valuation(pe_ratio=32.0),
                ),
                earnings=EarningsEvent(
                    ticker="AAPL",
                    earnings_date=date(2026, 7, 1),
                    days_to_earnings=13,
                ),
                news=[NewsItem(ticker="AAPL", title="New headline", publisher="X", link="", published=None)],
                filings=[SECFiling(
                    ticker="AAPL", form_type="8-K", filed_date=date(2026, 6, 18),
                    description="test", link="http://x", category="8-K",
                )],
            )
        ],
        portfolio_value=1550.0,
        portfolio_cost=1000.0,
        portfolio_pnl=550.0,
        portfolio_pnl_pct=55.0,
    )


def test_changes_detects_new_news_and_filings():
    prior = {
        "report_date": "2026-06-17",
        "tickers": [{
            "ticker": "AAPL",
            "daily_change_pct": 1.0,
            "valuation": {"pe_ratio": 30.0},
            "filing_ids": [],
            "news_titles": ["Old headline"],
            "earnings_date": "2026-07-01",
        }],
    }
    changes = compute_daily_changes(_report(), prior)
    assert changes.has_prior
    assert len(changes.ticker_changes) == 1
    tc = changes.ticker_changes[0]
    assert "New headline" in tc.new_news
    assert len(tc.new_filings) == 1
    assert any("P/E" in v for v in tc.valuation_changes)


def test_changes_no_prior():
    changes = compute_daily_changes(_report(), None)
    assert not changes.has_prior
    assert len(changes.ticker_changes) == 0
