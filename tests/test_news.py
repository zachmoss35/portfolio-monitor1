"""Tests for news relevance filtering."""

from datetime import datetime, timezone

from portfolio_agent.data.news import filter_relevant_news
from portfolio_agent.models import NewsItem
from portfolio_agent.utils.text_match import is_article_relevant


def _item(title: str, summary: str = "", link: str = "") -> NewsItem:
    return NewsItem(
        ticker="AAPL",
        title=title,
        publisher="Test",
        link=link,
        published=datetime(2026, 6, 18, tzinfo=timezone.utc),
        summary=summary,
    )


def test_relevant_when_ticker_in_title():
    assert is_article_relevant(title="AAPL beats earnings", ticker="AAPL")


def test_relevant_when_company_in_summary():
    assert is_article_relevant(
        title="Tech giant reports record quarter",
        summary="Apple Inc. posted strong iPhone sales",
        ticker="AAPL",
        company_name="Apple Inc.",
    )


def test_rejects_unrelated_provider_tagged_article():
    items = [
        _item("Tesla stock surges on delivery numbers", summary="TSLA shares rise"),
        _item("Apple beats Q2 earnings expectations", summary="AAPL revenue up"),
        _item("Microsoft cloud growth accelerates", summary="MSFT Azure gains"),
    ]
    filtered = filter_relevant_news(items, "AAPL", company_name="Apple Inc.")
    assert len(filtered) == 1
    assert "Apple" in filtered[0].title


def test_rejects_unrelated_ticker_mention_only_in_url():
    items = [
        _item(
            "Market roundup",
            summary="Stocks mixed ahead of Fed",
            link="https://example.com/news/nvda-amd-intc",
        ),
    ]
    filtered = filter_relevant_news(items, "AAPL", company_name="Apple Inc.")
    assert len(filtered) == 0


def test_relevant_when_ticker_in_url():
    items = [
        _item(
            "Earnings preview",
            summary="Analysts weigh in",
            link="https://example.com/stocks/aapl-earnings-preview",
        ),
    ]
    filtered = filter_relevant_news(items, "AAPL", company_name="Apple Inc.")
    assert len(filtered) == 1
