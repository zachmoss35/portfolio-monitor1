# VPS Deployment Guide

Deploy portfolio-monitor on a Linux VPS to generate and email reports every weekday at **6:00 AM Eastern**.

## Recommended providers

| Provider | Notes |
|----------|-------|
| [DigitalOcean](https://www.digitalocean.com/) | Simple droplets, good docs, $6/mo tier is enough |
| [Hetzner](https://www.hetzner.com/) | Low cost EU/US VPS, great value |
| [AWS Lightsail](https://aws.amazon.com/lightsail/) | Fixed-price instances, easy if you already use AWS |

Minimum spec: **1 vCPU, 1 GB RAM, Ubuntu 22.04+**. The app is lightweight.

## Quick deploy

```bash
# On the VPS
git clone <your-repo-url> portfolio-monitor
cd portfolio-monitor

bash deploy/setup_server.sh    # install deps, venv, dirs
nano .env                      # SMTP + SEC_USER_AGENT + optional keys
nano data/portfolio.csv        # your holdings

bash deploy/run_daily.sh       # manual test
python -m portfolio_agent.main health

bash deploy/install_cron.sh    # install weekday 6 AM cron
```

## Environment variables

Copy `.env.example` to `.env` and configure:

| Variable | Required | Notes |
|----------|----------|-------|
| `SMTP_USER` / `SMTP_PASSWORD` | For email | Gmail app password recommended |
| `EMAIL_TO` | For email | Report recipient |
| `SEC_USER_AGENT` | Recommended | `YourName your-email@example.com` |
| `NEWS_API_KEY` | Optional | Richer news via NewsAPI |
| `OPENAI_API_KEY` | Optional | AI analyst summaries |
| `USE_AI_SUMMARY` | Optional | `true` to enable AI (requires OpenAI key) |
| `MAX_NEWS_PER_TICKER` | Optional | Default `5` |
| `EARNINGS_LOOKAHEAD_DAYS` | Optional | Default `30` |
| `MATERIAL_MOVE_THRESHOLD` | Optional | Default `0.05` (5% move) |
| `TZ` | Recommended | `America/New_York` |

## Portfolio CSV format

**Extended schema** (recommended):

```csv
ticker,shares,cost_basis,company,sector,priority,notes
AAPL,50,175.00,Apple Inc.,Technology,high,Core holding
```

**Legacy schema** (still works):

```csv
ticker,shares,cost_basis,notes
AAPL,50,175.00,Core holding
```

## Timezone

The cron job fires at **6:00 AM server local time**. `setup_server.sh` sets the server to `America/New_York`.

Verify:

```bash
timedatectl
# or
date
```

If you cannot change the server timezone, set `TZ=America/New_York` in `.env` and adjust the cron hour manually. For example, a UTC server would need `0 11 * * 1-5` during EST (UTC-5).

## Scripts

| Script | Purpose |
|--------|---------|
| `setup_server.sh` | One-time VPS bootstrap: Python, venv, pip, git, dirs |
| `run_daily.sh` | Run report + email, append to `logs/daily.log`, write health markers |
| `install_cron.sh` | Install `0 6 * * 1-5 bash deploy/run_daily.sh` |

## Logs and health

| File | Meaning |
|------|---------|
| `logs/daily.log` | Full stdout/stderr from each cron run |
| `logs/last_success.txt` | ISO timestamp of last successful run |
| `logs/last_error.txt` | ISO timestamp + exit code of last failure |
| `reports/YYYY-MM-DD.md` | Generated daily reports |
| `snapshots/YYYY-MM-DD.json` | Data snapshots for day-over-day change tracking |

Check status:

```bash
python -m portfolio_agent.main health
tail -50 logs/daily.log
```

## Manual test commands

```bash
source .venv/bin/activate

# Generate report only (no email)
python -m portfolio_agent.main run

# Generate + email (same as cron)
python -m portfolio_agent.main email

# Full cron simulation
bash deploy/run_daily.sh

# Health check
python -m portfolio_agent.main health
```

## Updating on Lightsail (or any VPS)

```bash
cd portfolio-monitor
git pull
source .venv/bin/activate
pip install -r requirements.txt

# Verify before relying on cron
bash deploy/run_daily.sh
python -m portfolio_agent.main health
```

If you added new `.env` options, merge them from `.env.example`:

```bash
diff .env.example .env   # check for new variables
nano .env                # add any missing keys
```

No cron reinstall is needed after updates unless you moved the project directory.

## Troubleshooting

### Yahoo Finance failures

Yahoo Finance can rate-limit or block VPS IPs.

- Check `logs/daily.log` for `curl` or `ProxyError` messages
- Retry manually: `python -m portfolio_agent.main run -v`
- Ensure outbound HTTPS (port 443) is open
- If blocked, try a different VPS provider/region

### SEC EDGAR 403

SEC requires a valid `SEC_USER_AGENT` in `.env`:

```
SEC_USER_AGENT=YourName your-email@example.com
```

### Email not sending

- Verify SMTP credentials in `.env`
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)
- Test: `python -m portfolio_agent.main email -v`
- Check firewall allows outbound port 587

### AI summaries not working

- Confirm `OPENAI_API_KEY` is set and `USE_AI_SUMMARY=true`
- Check `logs/daily.log` for OpenAI API errors
- The agent runs normally without AI if the key is absent

### No day-over-day changes

- Requires prior snapshots in `snapshots/`
- First run creates a snapshot; changes appear on the second consecutive run
- Snapshots are created automatically — do not delete the directory

### Cron not running

```bash
crontab -l                          # verify entry exists
grep CRON /var/log/syslog           # Ubuntu cron logs
bash deploy/run_daily.sh            # test script directly
```

### Wrong run time

```bash
timedatectl                         # confirm timezone
cat .env | grep TZ                  # confirm TZ=America/New_York
```

## macOS / local dev

The built-in Python scheduler still works locally:

```bash
python -m portfolio_agent.main schedule
```

For production, prefer **cron on a VPS** over the long-running scheduler daemon.
