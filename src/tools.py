import yfinance as yf
from tavily import TavilyClient
from src.config import TAVILY_API_KEY, SEARCH_RESULTS_PER_STOCK

_tavily = TavilyClient(api_key=TAVILY_API_KEY)


def search_stock_news(ticker: str) -> list[dict]:
    """Return recent news articles for a ticker via Tavily."""
    queries = [
        f"{ticker} stock news today",
        f"{ticker} earnings catalyst analyst 2025",
    ]
    results = []
    for q in queries:
        response = _tavily.search(
            query=q,
            max_results=SEARCH_RESULTS_PER_STOCK,
            search_depth="advanced",
        )
        results.extend(response.get("results", []))
    # deduplicate by URL
    seen, unique = set(), []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
    return unique


def get_stock_snapshot(ticker: str) -> dict:
    """Return price, change %, market cap, and next earnings date."""
    info = yf.Ticker(ticker).info
    hist  = yf.Ticker(ticker).history(period="2d")

    price      = info.get("currentPrice") or info.get("regularMarketPrice")
    prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
    pct_change = ((price - prev_close) / prev_close * 100) if price and prev_close else None
    market_cap = info.get("marketCap")
    earnings   = info.get("earningsDate") or info.get("earningsTimestamp")

    return {
        "ticker":     ticker,
        "name":       info.get("longName", ticker),
        "price":      round(price, 2) if price else "N/A",
        "pct_change": round(pct_change, 2) if pct_change is not None else "N/A",
        "market_cap": market_cap,
        "sector":     info.get("sector", ""),
        "earnings_date": str(earnings) if earnings else "N/A",
    }
