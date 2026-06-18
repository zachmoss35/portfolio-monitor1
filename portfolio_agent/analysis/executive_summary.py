"""Executive summary generation."""

from __future__ import annotations

from portfolio_agent.config import Config
from portfolio_agent.models import DailyReport, ExecutiveSummary, Flag, TickerAnalysis


def build_executive_summary(
    analyses: list[TickerAnalysis],
    config: Config,
) -> ExecutiveSummary:
    """Build the top-of-report executive summary."""
    threshold_pct = config.material_move_threshold * 100
    summary = ExecutiveSummary()

    for a in analyses:
        ticker = a.holding.ticker
        name = a.market.company_name
        pct = a.market.daily_change_pct

        if pct >= threshold_pct:
            summary.top_positive.append(
                f"**{ticker}** ({name}): +{pct:.1f}% today"
            )
        elif pct <= -threshold_pct:
            summary.top_negative.append(
                f"**{ticker}** ({name}): {pct:.1f}% today"
            )

        if abs(pct) >= threshold_pct:
            summary.major_movers.append(
                f"**{ticker}**: {pct:+.1f}% ({name})"
            )

        if a.flag in (Flag.SELL, Flag.WATCH):
            summary.needs_review.append(f"**{ticker}**: {a.flag.value.upper()}")

        if a.earnings.within_30_days and a.earnings.earnings_date:
            flag = " ⚠️" if a.earnings.within_14_days else ""
            summary.upcoming_earnings.append(
                f"**{ticker}**: {a.earnings.earnings_date} "
                f"({a.earnings.days_to_earnings}d away){flag}"
            )

    # Sort movers by absolute daily change (stored in analyses order)
    summary.major_movers.sort(
        key=lambda s: abs(
            next(
                (a.market.daily_change_pct for a in analyses if a.holding.ticker in s),
                0,
            )
        ),
        reverse=True,
    )
    summary.upcoming_earnings.sort(
        key=lambda s: int(s.split("(")[1].split("d")[0]) if "d away" in s else 999
    )

    return summary


def enrich_report_with_summary(report: DailyReport, config: Config) -> DailyReport:
    """Attach executive summary to a DailyReport."""
    report.executive_summary = build_executive_summary(report.analyses, config)
    return report
