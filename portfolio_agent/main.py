#!/usr/bin/env python3
"""CLI entry point for the portfolio monitoring agent."""

from __future__ import annotations

import argparse
import logging
import sys

from portfolio_agent.agent import run_daily_report
from portfolio_agent.config import load_config
from portfolio_agent.email_sender import send_report_email
from portfolio_agent.health import print_health
from portfolio_agent.scheduler import run_once_and_email, start_scheduler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Portfolio monitoring agent — daily reports, screeners, and alerts."
    )
    parser.add_argument(
        "command",
        choices=["run", "email", "schedule", "health"],
        help="run: generate report | email: generate + send | schedule: daemon | health: status",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = load_config()

    if args.command == "run":
        _, markdown, path = run_daily_report(config)
        print(f"Report saved to {path}")
        return 0

    if args.command == "email":
        path = run_once_and_email(config)
        print(f"Report generated and emailed: {path}")
        return 0

    if args.command == "schedule":
        print(
            f"Starting scheduler — weekday reports at "
            f"{config.email_hour:02d}:{config.email_minute:02d} {config.report_timezone}"
        )
        start_scheduler(config)
        return 0

    if args.command == "health":
        return print_health(config)

    return 1


if __name__ == "__main__":
    sys.exit(main())
