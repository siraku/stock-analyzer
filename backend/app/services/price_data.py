from datetime import datetime, timedelta, timezone

import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from app.config import settings
from app.models.price_cache import PriceCache


def fetch_price_history(ticker: str, db: Session, period: str = "6mo") -> pd.DataFrame:
    """
    Return OHLCV DataFrame for a ticker.
    Uses DB cache; re-fetches from yfinance if cache is stale.
    """
    ticker = ticker.upper()
    ttl = timedelta(minutes=settings.price_cache_ttl_minutes)
    cutoff = datetime.now(timezone.utc) - ttl

    # Check most recent cached row
    latest = (
        db.query(PriceCache)
        .filter(PriceCache.ticker == ticker)
        .order_by(PriceCache.date.desc())
        .first()
    )

    # Determine if we need a fresh fetch
    needs_fetch = True
    if latest is not None:
        fetched_at = latest.fetched_at
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        if fetched_at > cutoff:
            needs_fetch = False

    if needs_fetch:
        _refresh_cache(ticker, db, period)

    return _load_from_cache(ticker, db)


def _refresh_cache(ticker: str, db: Session, period: str) -> None:
    raw = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    if raw.empty:
        return

    # Flatten multi-level columns if present
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    for idx, row in raw.iterrows():
        trade_date = idx.date() if hasattr(idx, "date") else idx

        existing = (
            db.query(PriceCache)
            .filter(PriceCache.ticker == ticker, PriceCache.date == trade_date)
            .first()
        )
        if existing:
            existing.open = float(row.get("Open", 0) or 0)
            existing.high = float(row.get("High", 0) or 0)
            existing.low = float(row.get("Low", 0) or 0)
            existing.close = float(row.get("Close", 0) or 0)
            existing.volume = int(row.get("Volume", 0) or 0)
            existing.fetched_at = now
        else:
            db.add(PriceCache(
                ticker=ticker,
                date=trade_date,
                open=float(row.get("Open", 0) or 0),
                high=float(row.get("High", 0) or 0),
                low=float(row.get("Low", 0) or 0),
                close=float(row.get("Close", 0) or 0),
                volume=int(row.get("Volume", 0) or 0),
                fetched_at=now,
            ))

    db.commit()


def _load_from_cache(ticker: str, db: Session) -> pd.DataFrame:
    rows = (
        db.query(PriceCache)
        .filter(PriceCache.ticker == ticker)
        .order_by(PriceCache.date.asc())
        .all()
    )
    if not rows:
        return pd.DataFrame()

    data = [
        {
            "Date": r.date,
            "Open": r.open,
            "High": r.high,
            "Low": r.low,
            "Close": r.close,
            "Volume": r.volume,
        }
        for r in rows
    ]
    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["Date"])
    df.set_index("Date", inplace=True)
    return df


def get_current_price(ticker: str, db: Session) -> float | None:
    """Return the most recent closing price from cache."""
    row = (
        db.query(PriceCache)
        .filter(PriceCache.ticker == ticker)
        .order_by(PriceCache.date.desc())
        .first()
    )
    return row.close if row else None
