#!/usr/bin/env bash
# Install a weekday cron job at 6:00 AM America/New_York.
# Requires the server timezone to be America/New_York (see setup_server.sh).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_daily.sh"

chmod +x "$RUN_SCRIPT"

CRON_LINE="0 6 * * 1-5 bash $RUN_SCRIPT"

echo "Installing cron job:"
echo "  $CRON_LINE"
echo ""
echo "This runs Monday–Friday at 6:00 AM when the server timezone is America/New_York."
echo ""

# Remove any previous portfolio-monitor cron entries, then add the new one.
(crontab -l 2>/dev/null | grep -v "deploy/run_daily.sh" || true; echo "$CRON_LINE") | crontab -

echo "Cron installed. Current crontab:"
crontab -l
