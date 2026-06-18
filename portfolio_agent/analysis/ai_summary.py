"""Optional OpenAI-powered analyst summaries."""

from __future__ import annotations

import json
import logging

import requests

from portfolio_agent.models import AISummary, TickerAnalysis

logger = logging.getLogger(__name__)

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def generate_ai_summary(
    analysis: TickerAnalysis,
    api_key: str,
    model: str = "gpt-4o-mini",
) -> AISummary | None:
    """Generate a concise analyst-style summary for one ticker."""
    context = _build_context(analysis)
    prompt = (
        "You are a buy-side equity research analyst. Based on the data below, "
        "provide a concise JSON response with exactly these keys:\n"
        '  "what_changed": brief summary of what changed\n'
        '  "why_it_matters": why it matters for the investment\n'
        '  "action_item": specific action item or "No action needed"\n'
        "Keep each value to 1-2 sentences. Return only valid JSON.\n\n"
        f"Data:\n{context}"
    )

    try:
        resp = requests.post(
            OPENAI_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 400,
            },
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        data = json.loads(content)
        return AISummary(
            what_changed=data.get("what_changed", ""),
            why_it_matters=data.get("why_it_matters", ""),
            action_item=data.get("action_item", ""),
        )
    except Exception:
        logger.exception("OpenAI summary failed for %s", analysis.holding.ticker)
        return None


def _build_context(analysis: TickerAnalysis) -> str:
    h = analysis.holding
    m = analysis.market
    lines = [
        f"Ticker: {h.ticker}",
        f"Company: {m.company_name}",
        f"Price: ${m.price:.2f} ({m.daily_change_pct:+.1f}% today)",
        f"30d change: {m.change_30d_pct}%",
        f"Flag: {analysis.flag.value}",
    ]
    if analysis.earnings.earnings_date:
        lines.append(
            f"Next earnings: {analysis.earnings.earnings_date} "
            f"({analysis.earnings.days_to_earnings}d away)"
        )
    if analysis.news:
        lines.append("Recent news:")
        for n in analysis.news[:3]:
            lines.append(f"  - {n.title}")
    if analysis.filings:
        lines.append("Recent filings:")
        for f in analysis.filings[:3]:
            lines.append(f"  - {f.category} ({f.filed_date}): {f.relevance_summary}")
    if analysis.screener_hits:
        lines.append("Screener hits:")
        for hit in analysis.screener_hits:
            lines.append(f"  - {hit.rule_name}: {hit.description}")
    return "\n".join(lines)
