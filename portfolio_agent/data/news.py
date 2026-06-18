"""Fetch recent news for portfolio tickers."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import requests
import yfinance as yf

from portfolio_agent.models import NewsItem
from portfolio_agent.utils.text_match import is_article_relevant

logger = logging.getLogger(__name__)

MATERIAL_KEYWORDS = [
    "earnings", "acquisition", "merger", "lawsuit", "fda", "sec",
    "guidance", "revenue", "profit", "loss", "ceo", "cfo", "resign",
    "bankruptcy", "dividend", "buyback", "recall", "investigation",
    "upgrade", "downgrade", "target", "forecast", "beat", "miss",
]


def filter_relevant_news(
    items: list[NewsItem],
    ticker: str,
    company_name: str = "",
    aliases: list[str] | None = None,
) -> list[NewsItem]:
    """Keep only articles that mention the ticker, company name, or a known alias."""
    relevant: list[NewsItem] = []
    for item in items:
        if is_article_relevant(
            title=item.title,
            summary=item.summary,
            description=item.summary,
            url=item.link,
            ticker=ticker,
            company_name=company_name,
            aliases=aliases,
        ):
            relevant.append(item)
    return relevant


def fetch_news(
    ticker: str,
    news_api_key: str | None = None,
    max_items: int = 5,
    days_back: int = 3,
    company_name: str = "",
    aliases: list[str] | None = None,
) -> list[NewsItem]:
    """Fetch recent news, preferring NewsAPI when a key is provided."""
    if news_api_key:
        items = _fetch_from_newsapi(ticker, news_api_key, max_items * 2, days_back)
        if items:
            return filter_relevant_news(items, ticker, company_name, aliases)[:max_items]
    items = _fetch_from_yahoo(ticker, max_items * 2)
    return filter_relevant_news(items, ticker, company_name, aliases)[:max_items]


def _fetch_from_yahoo(ticker: str, max_items: int) -> list[NewsItem]:
    items: list[NewsItem] = []
    try:
        stock = yf.Ticker(ticker)
        raw_news = stock.news or []
    except Exception:
        logger.exception("Failed to fetch Yahoo news for %s", ticker)
        return items

    for entry in raw_news[:max_items]:
        content = entry.get("content", entry)
        title = content.get("title", entry.get("title", ""))
        if not title:
            continue
        pub_date = None
        pub_str = content.get("pubDate") or entry.get("providerPublishTime")
        if pub_str:
            try:
                if isinstance(pub_str, (int, float)):
                    pub_date = datetime.fromtimestamp(pub_str, tz=timezone.utc)
                else:
                    pub_date = datetime.fromisoformat(str(pub_str).replace("Z", "+00:00"))
            except (ValueError, TypeError, OSError):
                pass

        link = ""
        if "canonicalUrl" in content:
            link = content["canonicalUrl"].get("url", "")
        link = link or entry.get("link", "")

        summary = content.get("summary", "") or content.get("description", "") or ""
        title_lower = title.lower()
        is_material = any(kw in title_lower for kw in MATERIAL_KEYWORDS)

        items.append(
            NewsItem(
                ticker=ticker,
                title=title,
                publisher=content.get("provider", {}).get("displayName", "Yahoo Finance"),
                link=link,
                published=pub_date,
                summary=summary,
                is_material=is_material,
            )
        )
    return items


def _fetch_from_newsapi(
    ticker: str, api_key: str, max_items: int, days_back: int
) -> list[NewsItem]:
    items: list[NewsItem] = []
    from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": ticker,
        "from": from_date,
        "sortBy": "publishedAt",
        "pageSize": max_items,
        "apiKey": api_key,
        "language": "en",
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
    except Exception:
        logger.exception("NewsAPI request failed for %s", ticker)
        return items

    for article in articles[:max_items]:
        title = article.get("title", "")
        if not title or title == "[Removed]":
            continue
        pub_date = None
        if article.get("publishedAt"):
            try:
                pub_date = datetime.fromisoformat(
                    article["publishedAt"].replace("Z", "+00:00")
                )
            except ValueError:
                pass
        description = article.get("description", "") or ""
        title_lower = title.lower()
        is_material = any(kw in title_lower for kw in MATERIAL_KEYWORDS)
        items.append(
            NewsItem(
                ticker=ticker,
                title=title,
                publisher=article.get("source", {}).get("name", "NewsAPI"),
                link=article.get("url", ""),
                published=pub_date,
                summary=description,
                is_material=is_material,
            )
        )
    return items
