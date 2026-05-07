# Stock News Digest

A LangGraph-powered daily pipeline that researches your stock watchlist and emails you a digest of news, upcoming catalysts, and price snapshots.

Built with **Claude** (Anthropic), **Tavily** search, and **yfinance** — runs automatically every weekday morning via GitHub Actions.

> **Note:** This is a linear pipeline, not an autonomous agent. Claude does not decide what to search or call — it receives pre-fetched articles and returns structured HTML. LangGraph is used for state management and orchestration, not agentic tool-calling.

---

## What it does

For each stock in your watchlist:
1. Fetches latest price, day/week % change, 7-day price history, and next earnings date (via yfinance)
2. Searches the web for today's news and sector context (via Tavily — 2 queries per ticker)
3. Sends the articles to Claude, which returns up to 3 news bullets + upcoming catalysts as HTML
4. Assembles everything into a formatted HTML email and sends it via Gmail SMTP

---

## Pipeline architecture

```
fetch_snapshots → research_stocks → compose_digest → send email
```

The pipeline is a `StateGraph` with a `DigestState` TypedDict flowing through three nodes:

| Node | What it does | Uses LLM? |
|---|---|---|
| `fetch_snapshots` | Calls yfinance for price, history, earnings | No |
| `research_stocks` | Calls Tavily for news, then Claude to summarize | Yes — one call per ticker |
| `compose_digest` | Builds the final HTML entirely in Python | No |

**Claude's role is narrow:** it receives pre-fetched article text and returns structured HTML (news bullets + catalyst list). It does not call tools, does not decide what to search, and does not loop. There is no `bind_tools`, no `ToolNode`, and no agent loop.

**The email contains:**
- Stock table — ticker, price, day %, week %, colored sparkline, next earnings with days-until countdown
- Notable News — Tavily answer summary, upcoming catalysts with dates, news bullets with source links
- Hardcoded disclaimer (assembled in Python, never passed through Claude)

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

### 5. Run

```bash
# Use the default watchlist from src/config.py
python main.py

# Override tickers on the fly
python main.py AAPL NVDA MSFT
```

---

## Automated daily emails via GitHub Actions

The workflow in `.github/workflows/daily_digest.yml` runs every weekday at **7:00 AM Israel time (05:00 UTC)**.

To enable it, add your secrets to GitHub:

1. Go to your repo → **Settings → Secrets and variables → Actions**
2. Add each variable from `.env.example` as a **Repository secret**

You can also trigger a run manually from the **Actions** tab → `Daily Stock Digest` → **Run workflow**.

---

## Project structure

```
stock-news-agent/
├── src/
│   ├── agent.py          # LangGraph pipeline (fetch → research → compose)
│   ├── tools.py          # yfinance snapshot + Tavily search + sparkline helpers
│   ├── email_sender.py   # Gmail SMTP sender
│   └── config.py         # Watchlist + env config
├── prompts/
│   └── prompts.py        # SYSTEM_PROMPT, RESEARCH_PROMPT, DISCLAIMER constants
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
