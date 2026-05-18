"""News headline fetchers — Yahoo Finance RSS + Reddit JSON."""
import feedparser
import requests
import time
from datetime import datetime
from config import DEFAULT_TICKERS, MAX_HEADLINES

HEADERS = {"User-Agent": "StockSentimentDashboard/1.0 (educational project)"}


def _parse_date(s: str) -> str:
    """Best-effort parse of various published date strings to ISO format."""
    if not s:
        return datetime.now().isoformat()
    for fmt in ("%a, %d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(s.strip(), fmt).isoformat()
        except ValueError:
            pass
    return datetime.now().isoformat()


def fetch_yahoo_rss(ticker: str) -> list[dict]:
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    try:
        feed = feedparser.parse(url)
        rows = []
        for entry in feed.entries[:MAX_HEADLINES]:
            rows.append({
                "ticker":    ticker,
                "title":     entry.get("title", "").strip(),
                "source":    "Yahoo Finance",
                "url":       entry.get("link", ""),
                "published": _parse_date(entry.get("published", "")),
            })
        return rows
    except Exception:
        return []


def fetch_reddit(ticker: str) -> list[dict]:
    url = (f"https://www.reddit.com/r/stocks/search.json"
           f"?q={ticker}&restrict_sr=on&sort=new&limit=25&t=week")
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            return []
        posts = r.json().get("data", {}).get("children", [])
        rows = []
        for p in posts[:MAX_HEADLINES]:
            d = p["data"]
            title = d.get("title", "").strip()
            if not title or len(title) < 10:
                continue
            rows.append({
                "ticker":    ticker,
                "title":     title,
                "source":    "Reddit r/stocks",
                "url":       "https://reddit.com" + d.get("permalink", ""),
                "published": datetime.fromtimestamp(
                    d.get("created_utc", time.time())).isoformat(),
            })
        return rows
    except Exception:
        return []


def fetch_all(tickers: list[str] | None = None,
              progress_cb=None) -> list[dict]:
    """
    Fetch Yahoo RSS + Reddit for every ticker.
    progress_cb(ticker, done, total) called after each ticker if provided.
    """
    tickers = tickers or DEFAULT_TICKERS
    all_rows = []
    for i, ticker in enumerate(tickers):
        rows  = fetch_yahoo_rss(ticker)
        rows += fetch_reddit(ticker)
        all_rows.extend(rows)
        if progress_cb:
            progress_cb(ticker, i + 1, len(tickers))
        time.sleep(0.3)   # polite throttle
    return all_rows
