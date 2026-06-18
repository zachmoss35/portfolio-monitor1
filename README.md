# Portfolio Monitor

A Python buy-side research assistant that monitors your stock portfolio daily — pulling prices, valuations, earnings, news, and SEC filings, running custom screeners, and emailing a Markdown report every weekday morning.

Designed for **local development** and **Linux VPS deployment** via cron.

## Features

- **Portfolio tracking** — reads holdings from `data/portfolio.csv` (legacy and extended schema)
- **Executive summary** — top positive/negative developments, companies needing review, earnings, major movers
- **Day-over-day changes** — compares today's data to the prior snapshot
- **Market data** — daily price change, market cap, volume, 30-day momentum, valuation ratios
- **Valuation flags** — expensive growth, cheap value, multiple expansion/compression, missing data
- **Earnings calendar** — next/last earnings date, days until report, 14/30-day flags
- **News** — relevance-filtered headlines with material-news detection (Yahoo Finance + optional NewsAPI)
- **SEC filings** — classified 10-K, 10-Q, 8-K, S-1, 424B, Form 4, DEF 14A with priority and summaries
- **AI analyst summaries** — optional OpenAI-powered briefs (disabled without API key)
- **Screeners** — configurable rules in `data/screener_rules.yaml`
- **Action flags** — buy / watch / sell / hold per ticker
- **Daily reports** — saved to `reports/YYYY-MM-DD.md`
- **Email delivery** — weekday morning emails via SMTP
- **VPS-ready** — cron-based deployment with health checks and run logging

## Quick Start (local)

### 1. Clone and install

```bash
cd portfolio-monitor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` with your SMTP credentials and optional API keys:

| Variable | Required | Description |
|----------|----------|-------------|
| `SMTP_HOST` | For email | SMTP server (default: `smtp.gmail.com`) |
| `SMTP_PORT` | For email | SMTP port (default: `587`) |
| `SMTP_USER` | For email | SMTP username |
| `SMTP_PASSWORD` | For email | SMTP password or app password |
| `EMAIL_FROM` | For email | Sender address |
| `EMAIL_TO` | For email | Recipient address |
| `NEWS_API_KEY` | Optional | [NewsAPI](https://newsapi.org) key for richer news |
| `SEC_USER_AGENT` | Recommended | Your name + email (required by SEC EDGAR) |
| `OPENAI_API_KEY` | Optional | OpenAI key for AI analyst summaries |
| `USE_AI_SUMMARY` | Optional | Enable AI summaries (`true`/`false`, default: `false`) |
| `MAX_NEWS_PER_TICKER` | Optional | Max news items per ticker (default: `5`) |
| `EARNINGS_LOOKAHEAD_DAYS` | Optional | Earnings calendar window (default: `30`) |
| `MATERIAL_MOVE_THRESHOLD` | Optional | Price move threshold for executive summary (default: `0.05` = 5%) |
| `TZ` | VPS | Timezone (default: `America/New_York`) |
| `REPORT_TIMEZONE` | Optional | Timezone for scheduler (default: `America/New_York`) |
| `EMAIL_HOUR` | Optional | Hour to send (default: `6`) |
| `EMAIL_MINUTE` | Optional | Minute to send (default: `0`) |

### 3. Set up your portfolio

**Extended schema** (optional metadata columns):

```csv
ticker,shares,cost_basis,company,sector,priority,notes
AAPL,50,175.00,Apple Inc.,Technology,high,Core tech holding
MSFT,30,380.00,Microsoft Corp.,Technology,high,Cloud & AI exposure
```

**Legacy schema** (still supported):

```csv
ticker,shares,cost_basis,notes
AAPL,50,175.00,Core tech holding
MSFT,30,380.00,Cloud & AI exposure
```

### 4. Customize screeners

Edit `data/screener_rules.yaml` to add or modify rules. Supported operators: `gt`, `gte`, `lt`, `lte`, `eq`, `between`, `in`, `not_in`.

Available fields: `daily_change_pct`, `change_30d_pct`, `pe_ratio`, `forward_pe`, `peg_ratio`, `price_to_book`, `price_to_sales`, `ev_to_ebitda`, `volume_ratio`, `days_to_earnings`, `market_cap`, `sector`, `industry`.

## Usage

```bash
# Generate today's report (saves to reports/YYYY-MM-DD.md)
python -m portfolio_agent.main run

# Generate report and email it
python -m portfolio_agent.main email

# Start weekday morning scheduler daemon (local dev)
python -m portfolio_agent.main schedule

# Check last run status, errors, and latest report
python -m portfolio_agent.main health

# Verbose logging
python -m portfolio_agent.main run -v
```

## VPS Deployment

Run automatically on a Linux VPS every weekday at **6:00 AM Eastern** using cron.

**Recommended providers:** [DigitalOcean](https://www.digitalocean.com/), [Hetzner](https://www.hetzner.com/), [AWS Lightsail](https://aws.amazon.com/lightsail/)

Minimum: 1 vCPU, 1 GB RAM, Ubuntu 22.04+.

```bash
git clone <your-repo-url> portfolio-monitor
cd portfolio-monitor

bash deploy/setup_server.sh     # install Python, venv, deps, create dirs
nano .env                       # SMTP + SEC_USER_AGENT + optional OPENAI_API_KEY
nano data/portfolio.csv         # your holdings

bash deploy/run_daily.sh        # manual test
python -m portfolio_agent.main health

bash deploy/install_cron.sh     # weekday 6 AM cron job
```

See [deploy/README.md](deploy/README.md) for full VPS setup, Lightsail updates, and troubleshooting.

### Cron schedule

`install_cron.sh` installs:

```cron
0 6 * * 1-5 bash /path/to/portfolio-monitor/deploy/run_daily.sh
```

This runs Monday–Friday at 6:00 AM when the server timezone is `America/New_York` (set automatically by `setup_server.sh`).

### Logs and health

| File | Purpose |
|------|---------|
| `logs/daily.log` | Full stdout/stderr from each run |
| `logs/last_success.txt` | Timestamp of last successful run |
| `logs/last_error.txt` | Timestamp of last failed run |
| `reports/YYYY-MM-DD.md` | Generated reports |
| `snapshots/YYYY-MM-DD.json` | Daily data snapshots for change tracking |

```bash
python -m portfolio_agent.main health
tail -50 logs/daily.log
```

## Project Structure

```
portfolio-monitor/
├── data/
│   ├── portfolio.csv          # Your holdings
│   └── screener_rules.yaml    # Screener rule definitions
├── deploy/
│   ├── setup_server.sh        # VPS bootstrap script
│   ├── install_cron.sh        # Install weekday cron job
│   ├── run_daily.sh           # Cron entrypoint (run + log + health)
│   └── README.md              # VPS deployment guide
├── portfolio_agent/
│   ├── config.py              # .env loading
│   ├── models.py              # Data classes
│   ├── portfolio.py           # CSV reader
│   ├── health.py              # Health check CLI
│   ├── analysis/              # Executive summary, changes, AI
│   ├── data/
│   │   ├── market_data.py     # Yahoo Finance prices & valuation
│   │   ├── earnings.py        # Earnings calendar
│   │   ├── news.py            # News fetching & relevance filtering
│   │   └── sec_filings.py     # SEC EDGAR filings
│   ├── screener.py            # Rule engine
│   ├── flags.py               # Buy/watch/sell logic
│   ├── report.py              # Markdown report generator
│   ├── email_sender.py        # SMTP email delivery
│   ├── agent.py               # Orchestrator
│   ├── scheduler.py           # Local dev scheduler daemon
│   └── main.py                # CLI entry point
├── reports/                   # Generated daily reports
├── snapshots/                 # JSON snapshots for day-over-day comparison
├── logs/                      # Run logs and health markers
├── tests/                     # Unit tests
├── requirements.txt
└── .env.example
```

## Running Tests

```bash
pytest tests/ -v
```

## Troubleshooting

### Yahoo Finance / API failures

- Check `logs/daily.log` for connection or rate-limit errors
- Run manually with verbose logging: `python -m portfolio_agent.main run -v`
- Ensure outbound HTTPS (port 443) is allowed on the VPS
- Yahoo may block some VPS IP ranges — try a different region or provider

### SEC EDGAR 403

Set a valid user-agent in `.env`:

```
SEC_USER_AGENT=YourName your-email@example.com
```

### Email not sending

- Verify SMTP credentials in `.env`
- For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833)
- Test: `python -m portfolio_agent.main email -v`

### AI summaries not appearing

- Set `OPENAI_API_KEY` in `.env`
- Set `USE_AI_SUMMARY=true`
- Without a key, the agent runs normally without AI sections

### No "What changed" section

- Day-over-day changes require at least one prior snapshot in `snapshots/`
- Run the agent on consecutive days, or manually keep prior JSON snapshots

### Cron not running

```bash
crontab -l
bash deploy/run_daily.sh
grep CRON /var/log/syslog
```

## Gmail Setup

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=your-email@gmail.com
```

## License

MIT
