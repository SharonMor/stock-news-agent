# Stock News Agent

A LangGraph-powered AI agent that researches your stock watchlist daily and emails you a digest of news, upcoming catalysts, and key investor insights.

Built with **Claude** (Anthropic), **Tavily** search, and **yfinance** — runs automatically every weekday morning via GitHub Actions.

---

## What it does

For each stock in your watchlist the agent:
1. Fetches the latest price, % change, market cap, and next earnings date
2. Searches the web for recent news and upcoming catalysts
3. Uses Claude to synthesize a focused investor briefing
4. Combines all briefings into a formatted HTML email and sends it to you

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/SharonMor/stock-news-agent.git
cd stock-news-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Fill in `.env`:

| Variable | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com/) (free tier available) |
| `GMAIL_USER` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (requires 2FA) |
| `EMAIL_RECIPIENT` | Where to send the digest |

### 4. Customize your watchlist

Edit `src/config.py` and update the `STOCKS` list with your tickers.

### 5. Run locally

```bash
python main.py

# or override tickers on the fly:
python main.py AAPL NVDA MSFT
```

---

## Automated daily emails via GitHub Actions

The workflow in `.github/workflows/daily_digest.yml` runs every weekday at **7:00 AM Israel time**.

To enable it, add your secrets to GitHub:

1. Go to your repo → **Settings → Secrets and variables → Actions**
2. Add each variable from `.env.example` as a **Repository secret**

You can also trigger a run manually from the **Actions** tab → `Daily Stock Digest` → **Run workflow**.

---

## Project structure

```
stock-news-agent/
├── src/
│   ├── agent.py          # LangGraph agent (fetch → research → compose)
│   ├── tools.py          # Tavily search + yfinance snapshot
│   ├── email_sender.py   # Gmail SMTP sender
│   └── config.py         # Watchlist + env config
├── prompts/
│   └── prompts.py        # System + research + digest prompts
├── .github/workflows/
│   └── daily_digest.yml  # Scheduled GitHub Action
├── main.py               # Entry point
├── requirements.txt
├── .env.example          # Template — copy to .env and fill in
└── .gitignore
```

---

## License

MIT — use freely with your own API credentials.
