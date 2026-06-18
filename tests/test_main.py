"""Tests for CLI commands."""

from datetime import date
from pathlib import Path
from unittest.mock import patch

from portfolio_agent.config import Config
from portfolio_agent.main import main
from portfolio_agent.models import DailyReport


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
        openai_api_key=None,
        use_ai_summary=False,
        max_news_per_ticker=5,
        earnings_lookahead_days=30,
        material_move_threshold=0.05,
        portfolio_path=tmp_path / "portfolio.csv",
        screener_path=tmp_path / "screener_rules.yaml",
        reports_dir=tmp_path / "reports",
        logs_dir=tmp_path / "logs",
        snapshots_dir=tmp_path / "snapshots",
    )


def test_run_command_generates_report(tmp_path: Path, capsys):
    cfg = _config(tmp_path)
    cfg.portfolio_path.write_text("ticker,shares,cost_basis,notes\nAAPL,10,100,\n")
    cfg.screener_path.write_text("rules: []\n")

    mock_report = DailyReport(
        report_date=date.today(),
        analyses=[],
        portfolio_value=0,
        portfolio_cost=0,
        portfolio_pnl=0,
        portfolio_pnl_pct=0,
    )

    with patch("portfolio_agent.main.load_config", return_value=cfg), \
         patch("portfolio_agent.main.run_daily_report", return_value=(mock_report, "# Report", str(tmp_path / "reports" / "test.md"))):
        code = main(["run"])
    assert code == 0
    assert "Report saved" in capsys.readouterr().out


def test_health_command_still_works(tmp_path: Path, capsys):
    cfg = _config(tmp_path)
    cfg.reports_dir.mkdir(parents=True)
    cfg.logs_dir.mkdir(parents=True)
    with patch("portfolio_agent.main.load_config", return_value=cfg):
        code = main(["health"])
    assert code == 0
    assert "Health Check" in capsys.readouterr().out
