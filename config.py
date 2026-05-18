"""Central configuration."""

DEFAULT_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META",
    "NVDA", "TSLA", "AMD", "NFLX", "JPM",
    "ORCL", "CRM", "UBER", "COIN", "PLTR",
]

TICKER_NAMES = {
    "AAPL":  "Apple",       "MSFT":  "Microsoft",  "GOOGL": "Alphabet",
    "AMZN":  "Amazon",      "META":  "Meta",        "NVDA":  "NVIDIA",
    "TSLA":  "Tesla",       "AMD":   "AMD",         "NFLX":  "Netflix",
    "JPM":   "JPMorgan",    "ORCL":  "Oracle",      "CRM":   "Salesforce",
    "UBER":  "Uber",        "COIN":  "Coinbase",    "PLTR":  "Palantir",
}

DB_PATH             = "data/sentiment.db"
REFRESH_INTERVAL_S  = 300        # auto-refresh every 5 minutes
MAX_HEADLINES       = 25         # headlines kept per ticker per fetch
HISTORY_DAYS        = 60         # days of price + sentiment history
SENTIMENT_THRESHOLD = 0.05       # VADER compound: neutral band ±0.05

# Sentiment label thresholds (VADER compound score)
BULL_STRONG =  0.25
BULL_MILD   =  0.05
BEAR_MILD   = -0.05
BEAR_STRONG = -0.25

# Colours
BG        = "#0a0a1a"
CARD_BG   = "rgba(18,18,42,0.95)"
BORDER    = "rgba(255,255,255,0.08)"
TEXT      = "#e2e2f0"
MUTED     = "#6b7280"
ACCENT    = "#7c3aed"
GREEN     = "#22c55e"
RED       = "#ef4444"
YELLOW    = "#f59e0b"
