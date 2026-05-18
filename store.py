"""SQLite persistence layer — headlines + price snapshots."""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from config import DB_PATH, HISTORY_DAYS


def _conn():
    Path(DB_PATH).parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    con = _conn()
    con.executescript("""
        CREATE TABLE IF NOT EXISTS headlines (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker     TEXT    NOT NULL,
            title      TEXT    NOT NULL,
            source     TEXT,
            url        TEXT,
            published  TEXT,
            fetched_at TEXT    DEFAULT (datetime('now','localtime')),
            compound   REAL,
            pos        REAL,
            neg        REAL,
            neu        REAL,
            label      TEXT,
            UNIQUE(ticker, title)
        );
        CREATE TABLE IF NOT EXISTS prices (
            ticker TEXT NOT NULL,
            date   TEXT NOT NULL,
            open   REAL, high REAL, low REAL, close REAL,
            volume INTEGER,
            pct_change REAL,
            PRIMARY KEY (ticker, date)
        );
        CREATE INDEX IF NOT EXISTS idx_h_ticker_date ON headlines(ticker, fetched_at);
        CREATE INDEX IF NOT EXISTS idx_p_ticker_date ON prices(ticker, date);
    """)
    con.commit()
    con.close()


def upsert_headlines(rows: list[dict]):
    if not rows:
        return
    con = _conn()
    for r in rows:
        try:
            con.execute("""
                INSERT OR IGNORE INTO headlines
                    (ticker, title, source, url, published,
                     compound, pos, neg, neu, label)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (r.get("ticker"), r.get("title"), r.get("source"),
                  r.get("url"), r.get("published"),
                  r.get("compound"), r.get("pos"), r.get("neg"),
                  r.get("neu"), r.get("label")))
        except Exception:
            pass
    con.commit()
    # Prune old rows
    cutoff = (datetime.now() - timedelta(days=HISTORY_DAYS)).isoformat()
    con.execute("DELETE FROM headlines WHERE fetched_at < ?", (cutoff,))
    con.commit()
    con.close()


def upsert_prices(rows: list[dict]):
    if not rows:
        return
    con = _conn()
    for r in rows:
        con.execute("""
            INSERT OR REPLACE INTO prices
                (ticker, date, open, high, low, close, volume, pct_change)
            VALUES (?,?,?,?,?,?,?,?)
        """, (r["ticker"], r["date"], r.get("open"), r.get("high"),
              r.get("low"), r.get("close"), r.get("volume"), r.get("pct_change")))
    con.commit()
    con.close()


def get_headlines(ticker: str | None = None, days: int = 7) -> pd.DataFrame:
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    con = _conn()
    if ticker:
        df = pd.read_sql("""
            SELECT * FROM headlines
            WHERE ticker=? AND fetched_at >= ?
            ORDER BY fetched_at DESC
        """, con, params=(ticker, cutoff))
    else:
        df = pd.read_sql("""
            SELECT * FROM headlines
            WHERE fetched_at >= ?
            ORDER BY fetched_at DESC
        """, con, params=(cutoff,))
    con.close()
    return df


def get_prices(ticker: str, days: int = 60) -> pd.DataFrame:
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    con = _conn()
    df = pd.read_sql("""
        SELECT * FROM prices
        WHERE ticker=? AND date >= ?
        ORDER BY date ASC
    """, con, params=(ticker, cutoff))
    con.close()
    return df


def get_sentiment_summary() -> pd.DataFrame:
    """Return latest 24h avg sentiment per ticker."""
    cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
    con = _conn()
    df = pd.read_sql("""
        SELECT ticker,
               AVG(compound)        AS avg_compound,
               COUNT(*)             AS n_headlines,
               SUM(CASE WHEN label='Bullish' OR label='Slightly Bullish'
                         THEN 1 ELSE 0 END) AS bullish_count,
               SUM(CASE WHEN label='Bearish' OR label='Slightly Bearish'
                         THEN 1 ELSE 0 END) AS bearish_count
        FROM headlines
        WHERE fetched_at >= ?
        GROUP BY ticker
    """, con, params=(cutoff,))
    con.close()
    return df


def get_daily_sentiment(ticker: str, days: int = 30) -> pd.DataFrame:
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    con = _conn()
    df = pd.read_sql("""
        SELECT DATE(fetched_at) AS date,
               AVG(compound)   AS avg_sentiment,
               COUNT(*)        AS n_headlines
        FROM headlines
        WHERE ticker=? AND fetched_at >= ?
        GROUP BY DATE(fetched_at)
        ORDER BY date ASC
    """, con, params=(ticker, cutoff))
    con.close()
    return df


def db_exists() -> bool:
    return Path(DB_PATH).exists() and Path(DB_PATH).stat().st_size > 0
