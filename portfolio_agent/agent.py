"""Orchestrate data collection and report generation."""

from __future__ import annotations

import logging
from datetime import date

from portfolio_agent.analysis.ai_summary import generate_ai_summary
from portfolio_agent.analysis.changes import compute_daily_changes
from portfolio_agent.analysis.executive_summary import build_executive_summary
from portfolio_agent.analysis.snapshot import (
    load_prior_snapshot,
    prior_valuation_for_ticker,
    save_snapshot,
)
from portfolio_agent.analysis.valuation_flags import compute_valuation_flags
from portfolio_agent.config import Config
from portfolio_agent.data.earnings import fetch_earnings
from portfolio_agent.data.market_data import fetch_market_snapshot
from portfolio_agent.data.news import fetch_news
from portfolio_agent.data.sec_filings import fetch_filings
from portfolio_agent.flags import apply_flags
from portfolio_agent.models import DailyReport, TickerAnalysis
from portfolio_agent.portfolio import load_portfolio
from portfolio_agent.report import generate_report, save_report
from portfolio_agent.screener import load_rules, run_screeners

logger = logging.getLogger(__name__)


def run_daily_report(config: Config, report_date: date | None = None) -> tuple[DailyReport, str, str]:
    """Collect data, run screeners, and generate the daily report.

    Returns (DailyReport, markdown_content, saved_path).
    """
    report_date = report_date or date.today()
    holdings = load_portfolio(config.portfolio_path)
    rules = load_rules(config.screener_path)
    prior_snapshot = load_prior_snapshot(config.snapshots_dir, report_date)

    analyses: list[TickerAnalysis] = []
    portfolio_value = 0.0
    portfolio_cost = 0.0

    for holding in holdings:
        ticker = holding.ticker
        logger.info("Processing %s", ticker)

        market = fetch_market_snapshot(ticker)
        if not market:
            logger.warning("Skipping %s — no market data", ticker)
            continue

        company_name = holding.company or market.company_name
        earnings = fetch_earnings(ticker, lookahead_days=config.earnings_lookahead_days)
        news = fetch_news(
            ticker,
            news_api_key=config.news_api_key,
            max_items=config.max_news_per_ticker,
            company_name=company_name,
        )
        filings = fetch_filings(ticker, user_agent=config.sec_user_agent)

        hits = run_screeners(rules, market, earnings)

        prior_val = prior_valuation_for_ticker(prior_snapshot, ticker)
        val_flags = compute_valuation_flags(market.valuation, prior_val)

        analysis = TickerAnalysis(
            holding=holding,
            market=market,
            earnings=earnings,
            news=news,
            filings=filings,
            screener_hits=hits,
            valuation_flags=val_flags,
        )

        if config.use_ai_summary and config.openai_api_key:
            analysis.ai_summary = generate_ai_summary(analysis, config.openai_api_key)

        analyses.append(analysis)
        portfolio_value += market.price * holding.shares
        portfolio_cost += holding.cost_basis * holding.shares

    apply_flags(analyses)

    portfolio_pnl = portfolio_value - portfolio_cost
    portfolio_pnl_pct = (portfolio_pnl / portfolio_cost * 100) if portfolio_cost else 0.0

    report = DailyReport(
        report_date=report_date,
        analyses=analyses,
        portfolio_value=portfolio_value,
        portfolio_cost=portfolio_cost,
        portfolio_pnl=portfolio_pnl,
        portfolio_pnl_pct=portfolio_pnl_pct,
        executive_summary=build_executive_summary(analyses, config),
        daily_changes=compute_daily_changes(
            DailyReport(
                report_date=report_date,
                analyses=analyses,
                portfolio_value=portfolio_value,
                portfolio_cost=portfolio_cost,
                portfolio_pnl=portfolio_pnl,
                portfolio_pnl_pct=portfolio_pnl_pct,
            ),
            prior_snapshot,
        ),
    )

    save_snapshot(report, config.snapshots_dir)

    markdown = generate_report(report, config)
    saved_path = save_report(markdown, config.reports_dir, report_date)

    return report, markdown, str(saved_path)
