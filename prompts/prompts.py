SYSTEM_PROMPT = """You are an elite equity research analyst. Your job is to read raw news
and financial data for a set of stocks and produce a concise, high-signal daily digest
for a retail investor.

Guidelines:
- Be direct and actionable. Skip fluff.
- Highlight catalysts (earnings, product launches, regulatory events, macro impacts).
- Flag risks clearly.
- Use your judgment to separate noise from signal.
- Format output as clean HTML (for email rendering).
"""

RESEARCH_PROMPT = """Here is the raw research data for {ticker} ({name}):

PRICE SNAPSHOT:
- Price: ${price}  ({pct_change}% today)
- Market Cap: {market_cap}
- Sector: {sector}
- Next Earnings: {earnings_date}

RAW NEWS ARTICLES:
{articles}

---
Write a focused investor briefing for {ticker} covering:
1. **Key News** — what happened in the last 48 hours that matters
2. **Upcoming Catalysts** — events or dates to watch
3. **What to Watch** — 1-2 sentences on the key risk or opportunity right now

Keep it under 200 words. Format as HTML with <h3>, <ul>, <li>, <b> tags."""

DIGEST_PROMPT = """You have researched the following stocks: {tickers}

Here are the individual briefings:

{briefings}

Now write the DAILY DIGEST email body in HTML:
- Start with a short 2-3 sentence market context paragraph
- Then include each stock briefing (already formatted)
- End with a 1-sentence closing note

Wrap everything in a clean <div style="font-family: Arial, sans-serif; max-width: 700px; margin: auto;">
Use a color-coded header: green for positive days, red for negative, gray for flat."""
