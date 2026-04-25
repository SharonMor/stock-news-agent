from __future__ import annotations

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import ANTHROPIC_API_KEY, STOCKS
from src.tools import search_stock_news, get_stock_snapshot
from prompts.prompts import SYSTEM_PROMPT, RESEARCH_PROMPT, DIGEST_PROMPT


llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=ANTHROPIC_API_KEY,
    max_tokens=4096,
)


class DigestState(TypedDict):
    stocks: list[str]
    snapshots: dict[str, dict]
    briefings: dict[str, str]
    digest_html: str
    error: str | None


# --- Node: fetch price snapshots for all stocks ---
def fetch_snapshots(state: DigestState) -> DigestState:
    snapshots = {}
    for ticker in state["stocks"]:
        try:
            snapshots[ticker] = get_stock_snapshot(ticker)
        except Exception as e:
            snapshots[ticker] = {"ticker": ticker, "name": ticker, "error": str(e)}
    return {**state, "snapshots": snapshots}


# --- Node: research each stock and generate a briefing ---
def research_stocks(state: DigestState) -> DigestState:
    briefings = {}
    for ticker in state["stocks"]:
        snap = state["snapshots"].get(ticker, {})
        try:
            articles = search_stock_news(ticker)
            articles_text = "\n\n".join(
                f"[{a.get('published_date', '')}] {a['title']}\n{a.get('content', a.get('snippet', ''))}"
                for a in articles[:8]
            )
            prompt = RESEARCH_PROMPT.format(
                ticker=ticker,
                name=snap.get("name", ticker),
                price=snap.get("price", "N/A"),
                pct_change=snap.get("pct_change", "N/A"),
                market_cap=snap.get("market_cap", "N/A"),
                sector=snap.get("sector", "N/A"),
                earnings_date=snap.get("earnings_date", "N/A"),
                articles=articles_text,
            )
            response = llm.invoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ])
            briefings[ticker] = response.content
        except Exception as e:
            briefings[ticker] = f"<p><b>{ticker}</b>: Research failed — {e}</p>"

    return {**state, "briefings": briefings}


# --- Node: combine briefings into final digest ---
def compose_digest(state: DigestState) -> DigestState:
    tickers = ", ".join(state["stocks"])
    all_briefings = "\n\n---\n\n".join(
        f"<h2>{t}</h2>\n{b}" for t, b in state["briefings"].items()
    )
    prompt = DIGEST_PROMPT.format(tickers=tickers, briefings=all_briefings)
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])
    return {**state, "digest_html": response.content}


def build_graph() -> StateGraph:
    graph = StateGraph(DigestState)
    graph.add_node("fetch_snapshots", fetch_snapshots)
    graph.add_node("research_stocks", research_stocks)
    graph.add_node("compose_digest", compose_digest)

    graph.set_entry_point("fetch_snapshots")
    graph.add_edge("fetch_snapshots", "research_stocks")
    graph.add_edge("research_stocks", "compose_digest")
    graph.add_edge("compose_digest", END)

    return graph.compile()


def run_agent(stocks: list[str] | None = None) -> str:
    app = build_graph()
    result = app.invoke({
        "stocks": stocks or STOCKS,
        "snapshots": {},
        "briefings": {},
        "digest_html": "",
        "error": None,
    })
    return result["digest_html"]
