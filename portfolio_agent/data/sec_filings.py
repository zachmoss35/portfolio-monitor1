"""Fetch SEC filings from EDGAR."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

import requests

from portfolio_agent.models import SECFiling

logger = logging.getLogger(__name__)

SEC_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

# Forms we track in reports
TRACKED_FORMS = {
    "8-K", "10-K", "10-Q", "DEF 14A", "S-1", "S-3", "424B", "424B2", "424B3",
    "424B4", "424B5", "4", "SC 13D", "SC 13G",
}

HIGH_PRIORITY_FORMS = {"8-K", "10-K", "10-Q", "S-1", "4"}

FORM_CATEGORIES = {
    "10-K": "10-K",
    "10-K/A": "10-K",
    "10-Q": "10-Q",
    "10-Q/A": "10-Q",
    "8-K": "8-K",
    "8-K/A": "8-K",
    "S-1": "S-1",
    "S-1/A": "S-1",
    "S-3": "S-1",
    "S-3/A": "S-1",
    "424B": "424B",
    "424B2": "424B",
    "424B3": "424B",
    "424B4": "424B",
    "424B5": "424B",
    "4": "Form 4",
    "4/A": "Form 4",
    "DEF 14A": "DEF 14A",
    "DEFA14A": "DEF 14A",
    "SC 13D": "SC 13D",
    "SC 13G": "SC 13G",
}

FORM_RELEVANCE = {
    "10-K": "Annual report — full-year financials, risk factors, and management discussion.",
    "10-Q": "Quarterly report — interim financials and material updates since last 10-K.",
    "8-K": "Current report — material event (earnings, M&A, leadership change, etc.).",
    "S-1": "Registration statement — new securities offering or IPO filing.",
    "424B": "Prospectus supplement — pricing/terms for a securities offering.",
    "Form 4": "Insider transaction — officer/director buy or sell activity.",
    "DEF 14A": "Proxy statement — shareholder votes, executive comp, board elections.",
    "SC 13D": "Activist/large holder disclosure — 5%+ stake with intent to influence.",
    "SC 13G": "Passive large holder disclosure — 5%+ stake without activist intent.",
}


def classify_filing(form_type: str) -> tuple[str, bool, str]:
    """Return (category, is_high_priority, relevance_summary) for a form type."""
    category = FORM_CATEGORIES.get(form_type, form_type)
    is_high = form_type in HIGH_PRIORITY_FORMS or category in HIGH_PRIORITY_FORMS
    summary = FORM_RELEVANCE.get(category, f"SEC filing ({form_type}) — review for material updates.")
    return category, is_high, summary


def _is_tracked_form(form_type: str) -> bool:
    if form_type in TRACKED_FORMS:
        return True
    category, _, _ = classify_filing(form_type)
    return category in {"10-K", "10-Q", "8-K", "S-1", "424B", "Form 4", "DEF 14A", "SC 13D", "SC 13G"}


class SECClient:
    """Client for SEC EDGAR API."""

    def __init__(self, user_agent: str):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def _get_cik_map(self) -> dict[str, str]:
        resp = self.session.get(SEC_TICKER_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {
            entry["ticker"].upper(): str(entry["cik_str"]).zfill(10)
            for entry in data.values()
        }

    def fetch_filings(
        self, ticker: str, days_back: int = 7, max_items: int = 10
    ) -> list[SECFiling]:
        """Fetch recent SEC filings for a ticker."""
        filings: list[SECFiling] = []
        try:
            cik_map = self._get_cik_map()
            cik = cik_map.get(ticker.upper())
            if not cik:
                logger.warning("No CIK found for %s", ticker)
                return filings

            url = SEC_SUBMISSIONS_URL.format(cik=cik)
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            recent = data.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            dates = recent.get("filingDate", [])
            descriptions = recent.get("primaryDocDescription", [])
            accessions = recent.get("accessionNumber", [])
            primary_docs = recent.get("primaryDocument", [])

            cutoff = date.today() - timedelta(days=days_back)

            for i, form in enumerate(forms):
                if len(filings) >= max_items:
                    break
                filed = _parse_date(dates[i]) if i < len(dates) else None
                if not filed or filed < cutoff:
                    continue

                accession = accessions[i].replace("-", "") if i < len(accessions) else ""
                doc = primary_docs[i] if i < len(primary_docs) else ""
                link = (
                    f"https://www.sec.gov/Archives/edgar/data/"
                    f"{int(cik)}/{accession}/{doc}"
                )
                desc = descriptions[i] if i < len(descriptions) else form
                category, is_high, relevance = classify_filing(form)

                filings.append(
                    SECFiling(
                        ticker=ticker,
                        form_type=form,
                        filed_date=filed,
                        description=desc or form,
                        link=link,
                        is_new=filed >= date.today() - timedelta(days=1),
                        category=category,
                        is_high_priority=is_high,
                        relevance_summary=relevance,
                    )
                )
        except Exception:
            logger.exception("Failed to fetch SEC filings for %s", ticker)
        return filings


def fetch_filings(
    ticker: str, user_agent: str, days_back: int = 7
) -> list[SECFiling]:
    """Convenience wrapper around SECClient."""
    client = SECClient(user_agent)
    return [
        f for f in client.fetch_filings(ticker, days_back=days_back)
        if _is_tracked_form(f.form_type) or f.is_new
    ]


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
