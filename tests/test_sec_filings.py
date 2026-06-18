"""Tests for SEC filing classification."""

from portfolio_agent.data.sec_filings import classify_filing


def test_classify_10k():
    cat, priority, summary = classify_filing("10-K")
    assert cat == "10-K"
    assert priority is True
    assert "Annual" in summary


def test_classify_8k():
    cat, priority, summary = classify_filing("8-K")
    assert cat == "8-K"
    assert priority is True
    assert "material" in summary.lower()


def test_classify_form_4():
    cat, priority, summary = classify_filing("4")
    assert cat == "Form 4"
    assert priority is True
    assert "Insider" in summary


def test_classify_424b():
    cat, priority, summary = classify_filing("424B5")
    assert cat == "424B"
    assert "Prospectus" in summary


def test_classify_def14a_not_high_priority():
    cat, priority, summary = classify_filing("DEF 14A")
    assert cat == "DEF 14A"
    assert priority is False
