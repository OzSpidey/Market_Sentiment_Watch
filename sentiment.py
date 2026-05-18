"""VADER-based sentiment scoring for financial headlines."""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from config import BULL_STRONG, BULL_MILD, BEAR_MILD, BEAR_STRONG

_va = SentimentIntensityAnalyzer()

# Financial domain boosters — VADER underweights these by default
_FINANCE_BOOSTERS = {
    "surge": 1.5, "soar": 1.5, "rally": 1.2, "breakout": 1.3,
    "beat": 1.2, "beats": 1.2, "record": 0.8, "upgrade": 1.3,
    "outperform": 1.2, "buyout": 0.9, "acquire": 0.5,
    "plunge": -1.5, "crash": -1.5, "tumble": -1.3, "plummet": -1.5,
    "miss": -1.2, "misses": -1.2, "downgrade": -1.3, "recall": -0.8,
    "lawsuit": -0.9, "fraud": -1.8, "layoff": -1.0, "layoffs": -1.0,
    "bankruptcy": -2.0, "default": -1.5, "warning": -0.8,
    "investigation": -1.0, "fine": -0.8, "penalty": -0.8,
    "cut": -0.5, "cuts": -0.5,
}

for word, boost in _FINANCE_BOOSTERS.items():
    _va.lexicon[word] = boost


def score(text: str) -> dict:
    """Return VADER scores + a label for a single headline."""
    s = _va.polarity_scores(text)
    c = s["compound"]
    if c >= BULL_STRONG:
        label = "Bullish"
    elif c >= BULL_MILD:
        label = "Slightly Bullish"
    elif c <= BEAR_STRONG:
        label = "Bearish"
    elif c <= BEAR_MILD:
        label = "Slightly Bearish"
    else:
        label = "Neutral"
    return {
        "compound": round(c, 4),
        "pos":      round(s["pos"], 4),
        "neg":      round(s["neg"], 4),
        "neu":      round(s["neu"], 4),
        "label":    label,
    }


def score_headlines(rows: list[dict]) -> list[dict]:
    """Add sentiment fields to a list of headline dicts in-place."""
    for row in rows:
        s = score(row.get("title", ""))
        row.update(s)
    return rows


def label_color(label: str) -> str:
    mapping = {
        "Bullish":          "#22c55e",
        "Slightly Bullish": "#86efac",
        "Neutral":          "#6b7280",
        "Slightly Bearish": "#fca5a5",
        "Bearish":          "#ef4444",
    }
    return mapping.get(label, "#6b7280")
