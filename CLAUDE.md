# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the agent (uses watchlist from src/config.py)
python main.py

# Run with custom tickers (overrides config watchlist)
python main.py AAPL NVDA TSLA

# Copy and fill in environment variables before running
cp .env.example .env
```

There are no tests and no linter configured.

## Architecture

The agent is a **linear 3-node LangGraph pipeline** defined in `src/agent.py`:

```
fetch_snapshots → research_stocks → compose_digest → END
```

State flows as a `DigestState` TypedDict — each node receives the full state and returns a merged update with `{**state, ...}`.

**Node responsibilities:**

- `fetch_snapshots` — calls `get_stock_snapshot()` (yfinance) for every ticker; stores results in `state["snapshots"]`. Each snapshot includes price, day %, week %, 7-day price history, and next earnings info (`earnings_info: {date, timing}`). Earnings date is sourced from `ticker.calendar` (not `info`) to reliably return upcoming-only dates.

- `research_stocks` — for each ticker, calls `search_stock_news()` (two Tavily queries with today's date in the query string + `include_answer="basic"`), then calls Claude with `RESEARCH_PROMPT`. Claude returns a response split by `---CATALYSTS---` into two parts. Each briefing is stored as `{"news": str, "catalysts": str, "answer": str}` in `state["briefings"]`. Empty string means no notable news.

- `compose_digest` — **no Claude call**. Builds the final HTML entirely in Python: `_build_table()` generates the stock table, `_build_notable_section()` renders per-ticker news/catalysts from briefings. The `DISCLAIMER` constant is appended directly in Python and is never passed through Claude.

**LLM:** `claude-sonnet-4-6` via `langchain-anthropic`, invoked as `llm.invoke([_system_message(), HumanMessage(...)])`. `_system_message()` injects today's date at call time so the model always has current date context.

**Email output structure:**
1. Stock table — ticker, price, day %, week %, colored Unicode sparkline (green/red per day), next earnings with days-until count and pre/post-market timing if within 7 days
2. Notable News section — per ticker: Tavily answer summary, upcoming catalysts with dates, notable news bullets (max 3, balanced pos/neg, each with clickable dated source link)
3. Hardcoded disclaimer

**Prompts** live in `prompts/prompts.py` as plain string constants (`SYSTEM_PROMPT`, `RESEARCH_PROMPT`, `DISCLAIMER`). `RESEARCH_PROMPT` uses `.format(ticker, name, articles)`.

**Config** (`src/config.py`): `STOCKS` list (edit to change watchlist), `SEARCH_RESULTS_PER_STOCK` (Tavily results per query — currently 5, two queries per ticker).

**Email** is sent via Gmail SMTP SSL on port 465 (`src/email_sender.py`). Requires a Gmail App Password (not the account password).

## Key design decisions

- `compose_digest` builds HTML in Python rather than via Claude — prevents Claude from dropping the disclaimer or mangling structure.
- Tavily queries include today's date (e.g. `"AAPL Apple Inc. stock news May 07, 2026"`) to surface fresh results.
- `ticker.calendar` is used for earnings dates instead of `info["earningsDate"]` — the latter frequently returns past dates.
- The sparkline in `generate_sparkline()` returns HTML `<span>` elements with inline color, not plain Unicode, so each bar is individually colored green/red.

## Environment Variables

All required — agent will crash without them:

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API |
| `TAVILY_API_KEY` | Web search |
| `GMAIL_USER` | Sender Gmail address |
| `GMAIL_APP_PASSWORD` | Gmail App Password (requires 2FA on account) |
| `EMAIL_RECIPIENT` | Where to send the digest |

## Automation

`.github/workflows/daily_digest.yml` runs `python main.py` every weekday at **05:00 UTC (07:00 Israel time)**. All environment variables must be set as GitHub repository secrets. Supports `workflow_dispatch` for manual runs.
