#!/usr/bin/env bash
# Bootstrap a fresh Linux VPS for portfolio-monitor.
# Run from the repo root: bash deploy/setup_server.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

echo "==> Portfolio Monitor — server setup"
echo "    Repo: $REPO_DIR"

if command -v apt-get >/dev/null 2>&1; then
  echo "==> Installing system packages (apt)..."
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3 python3-venv python3-pip git
elif command -v dnf >/dev/null 2>&1; then
  echo "==> Installing system packages (dnf)..."
  sudo dnf install -y python3 python3-pip git
elif command -v yum >/dev/null 2>&1; then
  echo "==> Installing system packages (yum)..."
  sudo yum install -y python3 python3-pip git
else
  echo "WARNING: No supported package manager found. Ensure python3, venv, pip, and git are installed."
fi

echo "==> Setting timezone to America/New_York (recommended for cron)..."
if command -v timedatectl >/dev/null 2>&1; then
  sudo timedatectl set-timezone America/New_York || true
  timedatectl
else
  echo "    timedatectl not available — set TZ=America/New_York in .env and deploy/run_daily.sh"
fi

echo "==> Creating Python virtual environment..."
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Creating data directories..."
mkdir -p reports logs data

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "==> Created .env from .env.example — edit it with your SMTP and API keys."
else
  echo "==> .env already exists — skipping."
fi

echo ""
echo "Setup complete."
echo ""
echo "Next steps:"
echo "  1. Edit .env with SMTP credentials and SEC_USER_AGENT"
echo "  2. Edit data/portfolio.csv with your holdings"
echo "  3. Test:  bash deploy/run_daily.sh"
echo "  4. Cron:   bash deploy/install_cron.sh"
