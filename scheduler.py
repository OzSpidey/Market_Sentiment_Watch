"""Background data refresh — runs every REFRESH_INTERVAL_S seconds."""
from apscheduler.schedulers.background import BackgroundScheduler
from config import DEFAULT_TICKERS, REFRESH_INTERVAL_S
import fetcher, sentiment, store, pricer
import threading, datetime

_lock      = threading.Lock()
_last_run  = None
_scheduler = None


def _refresh(tickers=None):
    global _last_run
    tickers = tickers or DEFAULT_TICKERS
    with _lock:
        # 1. Fetch headlines
        rows = fetcher.fetch_all(tickers)
        # 2. Score sentiment
        rows = sentiment.score_headlines(rows)
        # 3. Persist
        store.upsert_headlines(rows)
        # 4. Update prices
        price_rows = pricer.fetch_price_history(tickers, days=60)
        store.upsert_prices(price_rows)
        _last_run = datetime.datetime.now()


def start(tickers=None):
    global _scheduler
    store.init_db()
    # First-run fetch in a background thread so the server starts fast
    threading.Thread(target=_refresh, args=(tickers,), daemon=True).start()
    # Schedule recurring refresh
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _refresh, "interval",
        seconds=REFRESH_INTERVAL_S,
        args=[tickers],
        id="data_refresh",
        max_instances=1,
    )
    _scheduler.start()


def force_refresh(tickers=None):
    """Called by the dashboard 'Refresh Now' button."""
    threading.Thread(target=_refresh, args=(tickers,), daemon=True).start()


def last_run_str() -> str:
    if _last_run is None:
        return "Fetching data…"
    delta = datetime.datetime.now() - _last_run
    mins  = int(delta.total_seconds() // 60)
    secs  = int(delta.total_seconds() % 60)
    if mins == 0:
        return f"Updated {secs}s ago"
    return f"Updated {mins}m {secs}s ago"
