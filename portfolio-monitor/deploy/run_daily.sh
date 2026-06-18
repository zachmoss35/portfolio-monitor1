#!/usr/bin/env bash
# Run the daily portfolio report and email it.
# Called by cron on weekday mornings.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

export TZ="${TZ:-America/New_York}"

LOG_DIR="$REPO_DIR/logs"
mkdir -p "$LOG_DIR" "$REPO_DIR/reports"

TIMESTAMP="$(date -Iseconds)"
LOG_FILE="$LOG_DIR/daily.log"

echo "=== Run started: $TIMESTAMP ===" >> "$LOG_FILE"

# shellcheck disable=SC1091
source "$REPO_DIR/.venv/bin/activate"

set +e
python -m portfolio_agent.main email >> "$LOG_FILE" 2>&1
EXIT_CODE=$?
set -e

if [[ $EXIT_CODE -eq 0 ]]; then
  date -Iseconds > "$LOG_DIR/last_success.txt"
  echo "=== Run finished OK: $(date -Iseconds) ===" >> "$LOG_FILE"
else
  {
    date -Iseconds
    echo "exit_code=$EXIT_CODE"
  } > "$LOG_DIR/last_error.txt"
  echo "=== Run FAILED (exit $EXIT_CODE): $(date -Iseconds) ===" >> "$LOG_FILE"
  exit "$EXIT_CODE"
fi
