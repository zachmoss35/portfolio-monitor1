"""Fetch SEC filings from EDGAR."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

import requests

from portfolio_agent.models import SECFiling

logger = logging.getLogger(__name__)

SEC_TICKER_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

MATERIAL_FORMS = {"8-K", "10-K", "10-Q", "DEF 14A", "S-1", "S-3", "4", "SC 13D", "SC 13G"}


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
                if i >= max_items:
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

                filings.append(
                    SECFiling(
                        ticker=ticker,
                        form_type=form,
                        filed_date=filed,
                        description=desc or form,
                        link=link,
                        is_new=filed >= date.today() - timedelta(days=1),
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
        if f.form_type in MATERIAL_FORMS or f.is_new
    ]


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
