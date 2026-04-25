#!/usr/bin/env python3
"""
Entry point — run directly or via GitHub Actions cron.

Usage:
    python main.py                    # use default watchlist from config.py
    python main.py AAPL TSLA NVDA     # override with custom tickers
"""

import sys
from src.agent import run_agent
from src.email_sender import send_digest


def main():
    stocks = sys.argv[1:] or None  # optional CLI override
    print(f"Running stock digest agent...")

    html = run_agent(stocks)
    send_digest(html)


if __name__ == "__main__":
    main()
