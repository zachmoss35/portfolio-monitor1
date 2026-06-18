"""Weekday morning email scheduler."""

from __future__ import annotations

import logging
import time
from datetime import datetime

import pytz
import schedule

from portfolio_agent.agent import run_daily_report
from portfolio_agent.config import Config, load_config
from portfolio_agent.email_sender import send_report_email

logger = logging.getLogger(__name__)


def _is_weekday(dt: datetime) -> bool:
    return dt.weekday() < 5  # Mon=0 .. Fri=4


def _job(config: Config) -> None:
    """Run the daily report and email it."""
    tz = pytz.timezone(config.report_timezone)
    now = datetime.now(tz)

    if not _is_weekday(now):
        logger.info("Weekend — skipping report")
        return

    logger.info("Running scheduled daily report")
    _, markdown, path = run_daily_report(config)
    logger.info("Report saved to %s", path)

    subject = f"Portfolio Daily Report — {now.strftime('%Y-%m-%d')}"
    send_report_email(config, subject, markdown)


def start_scheduler(config: Config | None = None) -> None:
    """Block and run the weekday morning scheduler."""
    config = config or load_config()
    time_str = f"{config.email_hour:02d}:{config.email_minute:02d}"
    schedule.every().day.at(time_str).do(_job, config=config)
    logger.info(
        "Scheduler started — reports at %s %s on weekdays",
        time_str,
        config.report_timezone,
    )

    while True:
        schedule.run_pending()
        time.sleep(30)


def run_once_and_email(config: Config | None = None) -> str:
    """Generate report now and email if configured. Returns saved path."""
    config = config or load_config()
    _, markdown, path = run_daily_report(config)
    subject = f"Portfolio Daily Report — {datetime.now().strftime('%Y-%m-%d')}"
    send_report_email(config, subject, markdown)
    return path
