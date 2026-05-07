import yfinance as yf
from datetime import datetime, date
from tavily import TavilyClient
from src.config import TAVILY_API_KEY, SEARCH_RESULTS_PER_STOCK

_tavily = TavilyClient(api_key=TAVILY_API_KEY)


def search_stock_news(ticker: str, company_name: str = "") -> dict:
    today_str = date.today().strftime("%B %d, %Y")
    queries = [
        f"{ticker} {company_name} stock news {today_str}",
        f"{ticker} competitors sector news {today_str}",
    ]
    all_results = []
    answer = ""
    for i, q in enumerate(queries):
        response = _tavily.search(
            query=q,
            max_results=SEARCH_RESULTS_PER_STOCK,
            search_depth="advanced",
            include_answer="basic",
        )
        all_results.extend(response.get("results", []))
        if i == 0 and response.get("answer"):
            answer = response["answer"]
    seen, unique = set(), []
    for r in all_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
    return {"articles": unique, "answer": answer}


_TIMING_MAP = {"BMO": "pre-market", "AMC": "post-market", "TNS": "during market"}


def _next_earnings_info(t: yf.Ticker, info: dict) -> dict:
    """Returns {date: YYYY-MM-DD, timing: str} for next upcoming earnings."""
    today = date.today()
    earnings_date = None
    try:
        cal = t.calendar
        if cal:
            dates = cal.get("Earnings Date", [])
            if not isinstance(dates, list):
                dates = [dates]
            future = []
            for d in dates:
                try:
                    if hasattr(d, "date"):
                        d = d.date()
                    elif isinstance(d, (int, float)):
                        d = datetime.fromtimestamp(d).date()
                    else:
                        d = datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
                    if d >= today:
                        future.append(d)
                except Exception:
                    continue
            if future:
                earnings_date = min(future).strftime("%Y-%m-%d")
    except Exception:
        pass

    raw_timing = info.get("earningsCallTime") or info.get("earningsTiming") or ""
    timing = _TIMING_MAP.get(str(raw_timing).upper(), "")

    return {"date": earnings_date or "N/A", "timing": timing}


def get_stock_snapshot(ticker: str) -> dict:
    t = yf.Ticker(ticker)
    info = t.info
    hist = t.history(period="7d")

    price      = info.get("currentPrice") or info.get("regularMarketPrice")
    prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
    day_pct    = ((price - prev_close) / prev_close * 100) if price and prev_close else None

    history = []
    if not hist.empty:
        for dt, row in hist.iterrows():
            history.append({"date": str(dt.date()), "close": round(row["Close"], 2)})

    week_pct = None
    if len(history) >= 2:
        week_pct = (history[-1]["close"] - history[0]["close"]) / history[0]["close"] * 100

    return {
        "ticker":        ticker,
        "name":          info.get("longName", ticker),
        "price":         round(price, 2) if price else "N/A",
        "day_pct":       round(day_pct, 2) if day_pct is not None else "N/A",
        "week_pct":      round(week_pct, 2) if week_pct is not None else "N/A",
        "market_cap":    info.get("marketCap"),
        "sector":        info.get("sector", ""),
        "earnings_info": _next_earnings_info(t, info),
        "history":       history,
    }


def generate_sparkline(history: list[dict]) -> str:
    if len(history) < 2:
        return ""
    prices = [h["close"] for h in history]
    min_p  = min(prices)
    max_p  = max(prices)
    rng    = max_p - min_p or 1
    bars   = "▁▂▃▄▅▆▇█"
    result = ""
    for i, p in enumerate(prices):
        bar = bars[int((p - min_p) / rng * 7)]
        if i == 0:
            color = "#9ca3af"
        else:
            color = "#16a34a" if p >= prices[i - 1] else "#dc2626"
        result += f'<span style="color:{color}">{bar}</span>'
    return result


def fmt_market_cap(val) -> str:
    if not val:
        return "N/A"
    if val >= 1_000_000_000_000:
        return f"${val/1_000_000_000_000:.1f}T"
    if val >= 1_000_000_000:
        return f"${val/1_000_000_000:.1f}B"
    return f"${val/1_000_000:.0f}M"
