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

State flows as a `DigestState` TypedDict through all nodes — each node receives the full state and returns a partial update merged with `{**state, ...}`.

**Node responsibilities:**
- `fetch_snapshots` — calls `get_stock_snapshot()` (yfinance) for every ticker in parallel-ish (sequential loop); stores results in `state["snapshots"]`
- `research_stocks` — for each ticker, runs two Tavily searches then calls Claude with `RESEARCH_PROMPT` to produce a per-stock HTML briefing; stores in `state["briefings"]`
- `compose_digest` — calls Claude once more with all briefings combined, using `DIGEST_PROMPT`, to produce the final HTML email body

**LLM:** `claude-sonnet-4-6` via `langchain-anthropic`, invoked directly (not as a LangGraph tool-calling agent — just `llm.invoke([SystemMessage, HumanMessage])`).

**Prompts** live in `prompts/prompts.py` as plain Python string constants (`SYSTEM_PROMPT`, `RESEARCH_PROMPT`, `DIGEST_PROMPT`). `RESEARCH_PROMPT` and `DIGEST_PROMPT` use `.format()` placeholders.

**Config** (`src/config.py`): `STOCKS` list (edit to change watchlist), `SEARCH_RESULTS_PER_STOCK` (Tavily results per query per ticker — currently 5, two queries per ticker so up to 10 results before dedup).

**Email** is sent via Gmail SMTP SSL on port 465 (`src/email_sender.py`). Requires a Gmail App Password (not the account password).

## Environment Variables

All required — agent will crash without them:

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API |
| `TAVILY_API_KEY` | Web search |
| `GMAIL_USER` | Sender Gmail address |
| `GMAIL_APP_PASSWORD` | Gmail App Password (requires 2FA on account) |
| `EMAIL_RECIPIENT` | Destination email |

## Automation

`.github/workflows/daily_digest.yml` runs `python main.py` every weekday at **05:00 UTC (07:00 Israel time)**. All environment variables must be set as GitHub repository secrets. Supports `workflow_dispatch` for manual runs.
