"""Health check utilities for monitoring run status."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from portfolio_agent.config import Config, LOGS_DIR, REPORTS_DIR


@dataclass
class HealthStatus:
    last_success: str | None
    last_error: str | None
    latest_report: Path | None
    logs_dir: Path
    reports_dir: Path


def _read_timestamp(path: Path) -> str | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    return text or None


def _find_latest_report(reports_dir: Path) -> Path | None:
    if not reports_dir.is_dir():
        return None
    reports = sorted(reports_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return reports[0] if reports else None


def get_health_status(
    logs_dir: Path = LOGS_DIR,
    reports_dir: Path = REPORTS_DIR,
) -> HealthStatus:
    """Collect health status from log markers and report files."""
    return HealthStatus(
        last_success=_read_timestamp(logs_dir / "last_success.txt"),
        last_error=_read_timestamp(logs_dir / "last_error.txt"),
        latest_report=_find_latest_report(reports_dir),
        logs_dir=logs_dir,
        reports_dir=reports_dir,
    )


def write_success_marker(logs_dir: Path = LOGS_DIR) -> Path:
    """Write a success timestamp marker after a successful run."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    path = logs_dir / "last_success.txt"
    path.write_text(datetime.now().isoformat(timespec="seconds"), encoding="utf-8")
    return path


def write_error_marker(logs_dir: Path = LOGS_DIR, message: str | None = None) -> Path:
    """Write an error timestamp marker after a failed run."""
    logs_dir.mkdir(parents=True, exist_ok=True)
    path = logs_dir / "last_error.txt"
    timestamp = datetime.now().isoformat(timespec="seconds")
    path.write_text(f"{timestamp}\n{message or ''}".strip(), encoding="utf-8")
    return path


def format_health_report(status: HealthStatus) -> str:
    """Format health status for CLI output."""
    lines = [
        "Portfolio Monitor — Health Check",
        "================================",
        f"Logs dir:    {status.logs_dir}",
        f"Reports dir: {status.reports_dir}",
        "",
        f"Last success: {status.last_success or '(none)'}",
        f"Last error:   {status.last_error or '(none)'}",
        f"Latest report: {status.latest_report or '(none)'}",
    ]
    return "\n".join(lines)


def print_health(config: Config | None = None) -> int:
    """Print health status to stdout. Returns 0 if last run succeeded more recently than last error."""
    from portfolio_agent.config import load_config

    config = config or load_config()
    status = get_health_status(config.logs_dir, config.reports_dir)
    print(format_health_report(status))

    if status.last_success and status.last_error:
        try:
            success_dt = datetime.fromisoformat(status.last_success.split("\n")[0])
            error_dt = datetime.fromisoformat(status.last_error.split("\n")[0])
            return 0 if success_dt >= error_dt else 1
        except ValueError:
            pass

    if status.last_error and not status.last_success:
        return 1
    return 0
