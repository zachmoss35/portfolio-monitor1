"""Load configuration from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"


@dataclass(frozen=True)
class Config:
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    email_from: str
    email_to: str
    news_api_key: str | None
    sec_user_agent: str
    report_timezone: str
    email_hour: int
    email_minute: int
    portfolio_path: Path
    screener_path: Path
    reports_dir: Path
    logs_dir: Path


def load_config(env_path: Path | None = None) -> Config:
    """Load config from .env and return a Config object."""
    load_dotenv(env_path or PROJECT_ROOT / ".env")

    timezone = os.getenv("TZ") or os.getenv("REPORT_TIMEZONE", "America/New_York")
    os.environ.setdefault("TZ", timezone)

    return Config(
        smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.getenv("SMTP_USER", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        email_from=os.getenv("EMAIL_FROM", ""),
        email_to=os.getenv("EMAIL_TO", ""),
        news_api_key=os.getenv("NEWS_API_KEY") or None,
        sec_user_agent=os.getenv(
            "SEC_USER_AGENT", "PortfolioMonitor contact@example.com"
        ),
        report_timezone=os.getenv("REPORT_TIMEZONE", timezone),
        email_hour=int(os.getenv("EMAIL_HOUR", "6")),
        email_minute=int(os.getenv("EMAIL_MINUTE", "0")),
        portfolio_path=DATA_DIR / "portfolio.csv",
        screener_path=DATA_DIR / "screener_rules.yaml",
        reports_dir=REPORTS_DIR,
        logs_dir=LOGS_DIR,
    )
