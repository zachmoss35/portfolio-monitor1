"""Tests for health check utilities."""

from pathlib import Path

from portfolio_agent.config import DATA_DIR, Config
from portfolio_agent.health import (
    format_health_report,
    get_health_status,
    print_health,
    write_error_marker,
    write_success_marker,
)


def _config(tmp_path: Path) -> Config:
    return Config(
        smtp_host="",
        smtp_port=587,
        smtp_user="",
        smtp_password="",
        email_from="",
        email_to="",
        news_api_key=None,
        sec_user_agent="test",
        report_timezone="America/New_York",
        email_hour=6,
        email_minute=0,
        portfolio_path=DATA_DIR / "portfolio.csv",
        screener_path=DATA_DIR / "screener_rules.yaml",
        reports_dir=tmp_path,
        logs_dir=tmp_path,
    )


def test_write_success_marker(tmp_path: Path):
    path = write_success_marker(tmp_path)
    assert path.name == "last_success.txt"
    assert path.read_text().strip()


def test_write_error_marker(tmp_path: Path):
    path = write_error_marker(tmp_path, message="test failure")
    content = path.read_text()
    assert "test failure" in content


def test_get_health_status(tmp_path: Path):
    reports = tmp_path / "reports"
    logs = tmp_path / "logs"
    reports.mkdir()
    logs.mkdir()
    (reports / "2026-06-18.md").write_text("# report")
    write_success_marker(logs)

    status = get_health_status(logs_dir=logs, reports_dir=reports)
    assert status.last_success is not None
    assert status.last_error is None
    assert status.latest_report is not None


def test_format_health_report(tmp_path: Path):
    status = get_health_status(logs_dir=tmp_path, reports_dir=tmp_path)
    text = format_health_report(status)
    assert "Health Check" in text
    assert "(none)" in text


def test_print_health_no_markers(tmp_path: Path):
    assert print_health(_config(tmp_path)) == 0


def test_print_health_error_without_success(tmp_path: Path):
    write_error_marker(tmp_path, "boom")
    assert print_health(_config(tmp_path)) == 1
