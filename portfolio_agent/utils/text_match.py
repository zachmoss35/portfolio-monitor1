"""Text matching helpers for news relevance filtering."""

from __future__ import annotations

import re

# Common ticker aliases (ticker -> alternate names/symbols)
TICKER_ALIASES: dict[str, list[str]] = {
    "GOOGL": ["GOOG", "Alphabet", "Google"],
    "GOOG": ["GOOGL", "Alphabet", "Google"],
    "META": ["Facebook"],
    "BRK.B": ["Berkshire Hathaway", "BRK-B"],
    "BRK.A": ["Berkshire Hathaway", "BRK-A"],
}


def _word_present(text: str, term: str) -> bool:
    """Match a term as a whole word (case-insensitive)."""
    if not term or not text:
        return False
    pattern = rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])"
    return bool(re.search(pattern, text, re.IGNORECASE))


def _significant_company_words(company_name: str) -> list[str]:
    """Extract meaningful words from a company name for matching."""
    stop = {"inc", "corp", "corporation", "ltd", "limited", "plc", "co", "company", "the", "and", "&"}
    words = re.findall(r"[A-Za-z]{3,}", company_name)
    return [w for w in words if w.lower() not in stop]


def build_search_terms(
    ticker: str,
    company_name: str = "",
    extra_aliases: list[str] | None = None,
) -> list[str]:
    """Build search terms for relevance matching."""
    terms: list[str] = [ticker]
    if company_name:
        terms.append(company_name)
        terms.extend(_significant_company_words(company_name))
    terms.extend(TICKER_ALIASES.get(ticker.upper(), []))
    if extra_aliases:
        terms.extend(extra_aliases)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for t in terms:
        key = t.lower()
        if key not in seen and t.strip():
            seen.add(key)
            unique.append(t)
    return unique


def is_article_relevant(
    *,
    title: str = "",
    summary: str = "",
    description: str = "",
    url: str = "",
    ticker: str,
    company_name: str = "",
    aliases: list[str] | None = None,
) -> bool:
    """Return True if article text references the ticker, company, or a known alias."""
    combined = " ".join(filter(None, [title, summary, description, url]))
    if not combined.strip():
        return False

    terms = build_search_terms(ticker, company_name, aliases)

    for term in terms:
        if len(term) <= 4:
            if _word_present(combined, term):
                return True
        else:
            if term.lower() in combined.lower():
                return True
    return False
