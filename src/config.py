import os
from dotenv import load_dotenv

load_dotenv()

# --- Your stock watchlist (edit freely) ---
STOCKS = [
    "AMD",    # AMD
    "INTC",   # Intel
    "WIX",    # Wix
    "MSFT",   # Microsoft
    "ORCL",   # Oracle
    "OKLO",   # Oklo
    "SOFI",   # SoFi
    "NOW",    # ServiceNow
]

# --- Email ---
EMAIL_RECIPIENT    = os.environ["EMAIL_RECIPIENT"]
EMAIL_SENDER       = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

# --- API keys ---
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TAVILY_API_KEY    = os.environ["TAVILY_API_KEY"]

# --- Tuning ---
SEARCH_RESULTS_PER_STOCK = 5
