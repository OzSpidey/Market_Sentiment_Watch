"""Price data via yfinance — OHLCV history + current quote + earnings."""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time


def fetch_price_history(tickers: list[str], days: int = 60) -> list[dict]:
    """Return OHLCV rows for every ticker, ready for store.upsert_prices."""
    rows = []
    period = f"{days}d"
    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(period=period)
            if hist.empty:
                continue
            hist = hist.reset_index()
            hist["ticker"] = ticker
            hist["date"]   = hist["Date"].dt.strftime("%Y-%m-%d")
            hist["pct_change"] = hist["Close"].pct_change() * 100
            for _, r in hist.iterrows():
                rows.append({
                    "ticker":     ticker,
                    "date":       r["date"],
                    "open":       round(float(r["Open"]),  4),
                    "high":       round(float(r["High"]),  4),
                    "low":        round(float(r["Low"]),   4),
                    "close":      round(float(r["Close"]), 4),
                    "volume":     int(r["Volume"]),
                    "pct_change": round(float(r["pct_change"]), 4)
                                  if pd.notna(r["pct_change"]) else 0.0,
                })
            time.sleep(0.15)
        except Exception:
            pass
    return rows


def get_current_quotes(tickers: list[str]) -> dict[str, dict]:
    """Return {ticker: {price, prev_close, change, pct_change}} for UI cards."""
    result = {}
    try:
        data = yf.download(
            tickers, period="2d", interval="1d",
            auto_adjust=True, progress=False,
            threads=True,
        )
        closes = data["Close"] if len(tickers) > 1 else data[["Close"]]
        closes.columns = tickers if len(tickers) > 1 else tickers
        for t in tickers:
            try:
                series = closes[t].dropna()
                if len(series) < 1:
                    continue
                price      = float(series.iloc[-1])
                prev_close = float(series.iloc[-2]) if len(series) >= 2 else price
                change     = price - prev_close
                pct        = (change / prev_close * 100) if prev_close else 0
                result[t]  = {
                    "price":      round(price, 2),
                    "prev_close": round(prev_close, 2),
                    "change":     round(change, 2),
                    "pct_change": round(pct, 2),
                }
            except Exception:
                pass
    except Exception:
        pass
    return result


def get_earnings_calendar(tickers: list[str]) -> list[dict]:
    """Return upcoming earnings dates for tracked tickers."""
    rows = []
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            cal = t.calendar
            if cal is None:
                continue
            # calendar can be a dict or a DataFrame depending on yfinance version
            if isinstance(cal, dict):
                date = cal.get("Earnings Date")
                if date and len(date) > 0:
                    d = date[0] if hasattr(date[0], "strftime") else None
                    if d:
                        rows.append({
                            "ticker": ticker,
                            "earnings_date": d.strftime("%Y-%m-%d"),
                            "days_until": (d.date() - datetime.today().date()).days,
                        })
            elif isinstance(cal, pd.DataFrame):
                if "Earnings Date" in cal.index:
                    d = cal.loc["Earnings Date"].iloc[0]
                    if hasattr(d, "strftime"):
                        rows.append({
                            "ticker": ticker,
                            "earnings_date": d.strftime("%Y-%m-%d"),
                            "days_until": (d.date() - datetime.today().date()).days,
                        })
        except Exception:
            pass
        time.sleep(0.1)
    rows = [r for r in rows if 0 <= r.get("days_until", -1) <= 90]
    rows.sort(key=lambda r: r["days_until"])
    return rows
