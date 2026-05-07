from __future__ import annotations

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import ANTHROPIC_API_KEY, STOCKS
from src.tools import search_stock_news, get_stock_snapshot, generate_sparkline, fmt_market_cap
from datetime import date, datetime
from prompts.prompts import SYSTEM_PROMPT, RESEARCH_PROMPT, DISCLAIMER


def _system_message() -> SystemMessage:
    today = date.today().strftime("%B %d, %Y")
    return SystemMessage(content=f"Today is {today}.\n\n{SYSTEM_PROMPT}")


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


def fetch_snapshots(state: DigestState) -> DigestState:
    snapshots = {}
    for ticker in state["stocks"]:
        try:
            snapshots[ticker] = get_stock_snapshot(ticker)
        except Exception as e:
            snapshots[ticker] = {"ticker": ticker, "name": ticker, "error": str(e)}
    return {**state, "snapshots": snapshots}


def research_stocks(state: DigestState) -> DigestState:
    briefings = {}
    for ticker in state["stocks"]:
        snap = state["snapshots"].get(ticker, {})
        try:
            search     = search_stock_news(ticker, company_name=snap.get("name", ""))
            articles   = search["articles"]
            answer     = search["answer"]
            articles_text = "\n\n".join(
                f"DATE: {a.get('published_date') or 'date-unknown'} | URL: {a.get('url', '')} | TITLE: {a['title']}\n{a.get('content', a.get('snippet', ''))}"
                for a in articles[:8]
            )
            prompt = RESEARCH_PROMPT.format(
                ticker=ticker,
                name=snap.get("name", ticker),
                articles=articles_text,
            )
            response = llm.invoke([
                _system_message(),
                HumanMessage(content=prompt),
            ])
            content = response.content.strip()
            if "---CATALYSTS---" in content:
                news_part, catalysts_part = content.split("---CATALYSTS---", 1)
                news_part = news_part.strip()
                catalysts_part = catalysts_part.strip()
            else:
                news_part, catalysts_part = content, ""
            briefings[ticker] = {
                "news":      "" if news_part == "NO_NEWS" else news_part,
                "catalysts": catalysts_part,
                "answer":    answer,
            }
        except Exception as e:
            briefings[ticker] = {"news": "", "catalysts": "", "answer": ""}

    return {**state, "briefings": briefings}


def _pct_html(val) -> str:
    if val == "N/A":
        return '<span style="color:#6b7280;">N/A</span>'
    color = "#16a34a" if float(val) >= 0 else "#dc2626"
    sign  = "+" if float(val) > 0 else ""
    return f'<span style="color:{color};font-weight:600;">{sign}{val}%</span>'


def _earnings_html(earnings_info: dict) -> str:
    earnings_date = earnings_info.get("date", "N/A")
    timing        = earnings_info.get("timing", "")
    if earnings_date == "N/A":
        return '<span style="color:#9ca3af;">N/A</span>'
    try:
        dt    = datetime.strptime(earnings_date, "%Y-%m-%d").date()
        label = dt.strftime("%b %d, %Y")
        days  = (dt - date.today()).days
        if days < 0:
            return '<span style="color:#9ca3af;">N/A</span>'
        days_label = f"in {days} day{'s' if days != 1 else ''}"
        timing_label = f" · {timing}" if timing and days <= 7 else ""
        return f'<span style="color:#111;">{label}</span> <span style="color:#6b7280;font-size:11px;">({days_label}{timing_label})</span>'
    except Exception:
        return f'<span style="color:#6b7280;">{earnings_date}</span>'


def _build_table(snapshots: dict) -> str:
    rows = ""
    for ticker, snap in snapshots.items():
        spark = generate_sparkline(snap.get("history", []))
        rows += (
            f'<tr style="border-bottom:1px solid #f3f4f6;">'
            f'<td style="padding:8px 12px;font-weight:700;">{ticker}</td>'
            f'<td style="padding:8px 12px;">${snap.get("price","N/A")}</td>'
            f'<td style="padding:8px 12px;">{_pct_html(snap.get("day_pct","N/A"))}</td>'
            f'<td style="padding:8px 12px;">{_pct_html(snap.get("week_pct","N/A"))}</td>'
            f'<td style="padding:8px 12px;font-family:monospace;letter-spacing:1px;color:#6b7280;">{spark}</td>'
            f'<td style="padding:8px 12px;font-size:12px;">{_earnings_html(snap.get("earnings_info",{"date":"N/A","timing":""}))}</td>'
            f'</tr>'
        )
    return (
        '<table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:24px;">'
        '<thead><tr style="background:#f9fafb;text-align:left;">'
        '<th style="padding:8px 12px;color:#6b7280;font-weight:600;">Ticker</th>'
        '<th style="padding:8px 12px;color:#6b7280;font-weight:600;">Price</th>'
        '<th style="padding:8px 12px;color:#6b7280;font-weight:600;">Day</th>'
        '<th style="padding:8px 12px;color:#6b7280;font-weight:600;">Week</th>'
        '<th style="padding:8px 12px;color:#6b7280;font-weight:600;">7-Day</th>'
        '<th style="padding:8px 12px;color:#6b7280;font-weight:600;">Next Earnings</th>'
        '</tr></thead>'
        f'<tbody>{rows}</tbody>'
        '</table>'
    )


def _build_notable_section(briefings: dict) -> str:
    label_style = "font-size:11px;font-weight:600;color:#9ca3af;text-transform:uppercase;letter-spacing:0.05em;margin:8px 0 2px;"
    blocks = ""
    for ticker, parts in briefings.items():
        news      = parts.get("news", "").strip()
        catalysts = parts.get("catalysts", "").strip()
        if not news and not catalysts:
            continue
        answer = parts.get("answer", "").strip()
        inner = ""
        if answer:
            inner += f'<p style="font-size:12px;color:#374151;margin:2px 0 8px;font-style:italic;">{answer}</p>'
        if catalysts:
            inner += f'<p style="{label_style}">Upcoming Catalysts</p>{catalysts}'
        if news:
            inner += f'<p style="{label_style}">Notable News</p>{news}'
        blocks += (
            f'<div style="margin-bottom:24px;padding-bottom:16px;border-bottom:1px solid #f3f4f6;">'
            f'<h3 style="font-size:14px;margin-bottom:4px;margin-top:0;">{ticker}</h3>'
            f'{inner}'
            f'</div>'
        )
    return blocks or '<p style="color:#6b7280;font-size:13px;">No major news today.</p>'


def compose_digest(state: DigestState) -> DigestState:
    today = date.today().strftime("%B %d, %Y")
    table_html   = _build_table(state["snapshots"])
    notable_html = _build_notable_section(state["briefings"])

    html = f"""<div style="font-family:Arial,sans-serif;max-width:680px;margin:auto;color:#111;padding:16px;">
<h1 style="font-size:20px;margin-bottom:2px;">Daily Stock Digest</h1>
<p style="color:#6b7280;font-size:13px;margin-top:0;margin-bottom:20px;">{today}</p>
{table_html}
<h2 style="font-size:15px;margin-bottom:12px;border-bottom:1px solid #e5e7eb;padding-bottom:6px;">Notable News</h2>
{notable_html}
{DISCLAIMER}
</div>"""

    return {**state, "digest_html": html}


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
