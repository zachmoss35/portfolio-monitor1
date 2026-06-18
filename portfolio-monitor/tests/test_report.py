"""Tests for Markdown report generation."""

from datetime import date

from portfolio_agent.models import (
    DailyReport,
    EarningsEvent,
    Flag,
    Holding,
    MarketSnapshot,
    NewsItem,
    SECFiling,
    ScreenerHit,
    TickerAnalysis,
    Valuation,
)
from portfolio_agent.report import generate_report, save_report


def _analysis(ticker: str = "AAPL", flag: Flag = Flag.HOLD) -> TickerAnalysis:
    return TickerAnalysis(
        holding=Holding(ticker=ticker, shares=10, cost_basis=100.0, notes="test"),
        market=MarketSnapshot(
            ticker=ticker,
            company_name="Apple Inc.",
            price=150.0,
            previous_close=148.0,
            daily_change=2.0,
            daily_change_pct=1.35,
            market_cap=3e12,
            volume=50_000_000,
            avg_volume=40_000_000,
            volume_ratio=1.25,
            change_30d_pct=5.0,
            valuation=Valuation(pe_ratio=30.0, forward_pe=28.0),
        ),
        earnings=EarningsEvent(ticker=ticker, earnings_date=date(2026, 7, 1), days_to_earnings=13),
        news=[NewsItem(ticker=ticker, title="Apple beats earnings", publisher="Reuters", link="http://x", published=None, is_material=True)],
        filings=[SECFiling(ticker=ticker, form_type="8-K", filed_date=date.today(), description="Current report", link="http://sec", is_new=True)],
        screener_hits=[ScreenerHit(ticker=ticker, rule_name="vol_spike", description="Volume up", severity=Flag.WATCH, field="volume_ratio", actual_value=1.25)],
        flag=flag,
    )


def test_generate_report_contains_sections():
    report = DailyReport(
        report_date=date(2026, 6, 18),
        analyses=[_analysis()],
        portfolio_value=1500.0,
        portfolio_cost=1000.0,
        portfolio_pnl=500.0,
        portfolio_pnl_pct=50.0,
    )
    md = generate_report(report)
    assert "# Portfolio Daily Report" in md
    assert "## Portfolio Summary" in md
    assert "## Action Flags" in md
    assert "## Portfolio Company Updates" in md
    assert "## Valuation Metrics" in md
    assert "## Earnings Calendar" in md
    assert "## New SEC Filings" in md
    assert "## Material News" in md
    assert "## Screener Results" in md
    assert "AAPL" in md


def test_save_report(tmp_path):
    path = save_report("# Test\n", tmp_path, date(2026, 6, 18))
    assert path.name == "2026-06-18.md"
    assert path.read_text() == "# Test\n"
