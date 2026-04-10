# Cyber Intel Dashboard

> Automated cyber threat intelligence feed. Scrapes 23 security sources hourly, scores by threat severity, deploys to a live dashboard.

## Architecture

```
GitHub Repository
  └── .github/workflows/scrape.yml   ← Cron: every hour
        │
        ▼
  GitHub Actions Runner (free, ubuntu)
        │
        ▼
  scraper/main.py
    ├── sources.py    → 23 cyber RSS feeds (Krebs, CISA, THN, BleepingComputer...)
    ├── scoring.py    → BM25 keyword scoring + critical theme detection
    ├── storage.py    → 7-day sliding window, dedup, persist
    ├── alerts.py     → Telegram alerts for critical items
    └── (generates)  → data.json + index.html
        │
        ▼
  git commit + push (only if changed)
        │
        ▼
  Vercel (auto-deploy on push) → your-domain.vercel.app
```

## Scoring

Articles are scored 0–100 using BM25 with a weighted cyber threat taxonomy:

| Score | Level    | Examples |
|-------|----------|---------|
| 80+   | Critical | Zero-day, ransomware, nation-state attacks |
| 65–79 | High     | Active exploits, RCE, data breaches |
| 50–64 | Medium   | CVEs, phishing campaigns, advisories |
| <50   | Low      | General security news |

**Critical theme override**: articles mentioning zero-day, ransomware, supply chain attack, wiper, RCE, etc. are always surfaced regardless of score.

## Sources (23 feeds)

Krebs on Security, Schneier on Security, The Hacker News, BleepingComputer, Dark Reading, SecurityWeek, Threatpost, Recorded Future, Mandiant Blog, Google Project Zero, Talos Intelligence, Rapid7, Malwarebytes Labs, Sophos News, SANS Internet Storm Center, CISA Advisories, US-CERT, NVD CVE Feed, CyberScoop, ZDNet Security, Ars Technica Security, Troy Hunt, NCSC UK.

## Setup

### 1. Fork this repo

Click **Fork** on GitHub.

### 2. Deploy to Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New Project**
2. Import your fork
3. Deploy (auto-detects static site)

### 3. Enable GitHub Actions

Go to **Actions** tab in your fork → click **Enable workflows**.

The scraper runs every hour automatically. First run populates `data.json`.

### 4. Telegram alerts (optional)

Add these as **Repository Secrets** (Settings → Secrets → Actions):

| Secret | Value |
|--------|-------|
| `TELEGRAM_BOT_TOKEN` | From @BotFather on Telegram |
| `TELEGRAM_CHAT_ID`   | Your chat or channel ID |

Without these, the scraper still works — just no push notifications.

## Running locally

```bash
cd scraper
python main.py
# Opens data.json in the root — serve index.html with any static server
python -m http.server 8080  # from repo root
```

## Cost

**€0** — GitHub Actions free tier + Vercel free tier.

## Customising

- **Add/remove sources**: edit `scraper/sources.py`
- **Tune scoring**: edit keyword weights in `scraper/scoring.py`
- **Change categories**: edit `CATEGORY_TAGS` in `scraper/scoring.py`
- **Dashboard styling**: edit `index.html`
