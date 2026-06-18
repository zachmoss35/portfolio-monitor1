"""Tests for executive summary generation."""

from __future__ import annotations

from datetime import date

from portfolio_agent.analysis.executive_summary import build_executive_summary
from portfolio_agent.config import Config
from portfolio_agent.models import (
    EarningsEvent,
    Flag,
    Holding,
    MarketSnapshot,
    TickerAnalysis,
)


def _config() -> Config:
    return Config(
        smtp_host="",
        smtp_port=587,
        smtp_user="",
        smtp_password="",
        email_from="",
        email_to="",
        news_api_key=None,
        sec_user_agent="test",
        report_timezone="America/New_York",
        email_hour=6,
        email_minute=0,
        openai_api_key=None,
        use_ai_summary=False,
        max_news_per_ticker=5,
        earnings_lookahead_days=30,
        material_move_threshold=0.05,
        portfolio_path=__import__("pathlib").Path("data/portfolio.csv"),
        screener_path=__import__("pathlib").Path("data/screener_rules.yaml"),
        reports_dir=__import__("pathlib").Path("reports"),
        logs_dir=__import__("pathlib").Path("logs"),
        snapshots_dir=__import__("pathlib").Path("snapshots"),
    )


def _analysis(
    ticker: str,
    daily_pct: float,
    flag: Flag = Flag.HOLD,
    days_to_earnings: int | None = None,
) -> TickerAnalysis:
    earn_date = date(2026, 7, 1) if days_to_earnings is not None else None
    return TickerAnalysis(
        holding=Holding(ticker=ticker, shares=10, cost_basis=100.0),
        market=MarketSnapshot(
            ticker=ticker,
            company_name=f"{ticker} Corp",
            price=100.0,
            previous_close=100.0,
            daily_change=daily_pct,
            daily_change_pct=daily_pct,
            market_cap=1e9,
            volume=1_000_000,
            avg_volume=1_000_000,
            volume_ratio=1.0,
            change_30d_pct=0.0,
        ),
        earnings=EarningsEvent(
            ticker=ticker,
            earnings_date=earn_date,
            days_to_earnings=days_to_earnings,
            within_14_days=days_to_earnings is not None and days_to_earnings <= 14,
            within_30_days=days_to_earnings is not None and days_to_earnings <= 30,
        ),
        flag=flag,
    )


def test_executive_summary_positive_movers():
    analyses = [_analysis("AAPL", 6.0), _analysis("MSFT", 1.0)]
    summary = build_executive_summary(analyses, _config())
    assert len(summary.top_positive) == 1
    assert "AAPL" in summary.top_positive[0]


def test_executive_summary_negative_movers():
    analyses = [_analysis("NVDA", -7.0)]
    summary = build_executive_summary(analyses, _config())
    assert len(summary.top_negative) == 1
    assert "NVDA" in summary.top_negative[0]


def test_executive_summary_needs_review():
    analyses = [_analysis("JPM", 0.0, flag=Flag.SELL)]
    summary = build_executive_summary(analyses, _config())
    assert len(summary.needs_review) == 1
    assert "JPM" in summary.needs_review[0]


def test_executive_summary_upcoming_earnings():
    analyses = [_analysis("GOOGL", 0.0, days_to_earnings=10)]
    summary = build_executive_summary(analyses, _config())
    assert len(summary.upcoming_earnings) == 1
    assert "GOOGL" in summary.upcoming_earnings[0]
