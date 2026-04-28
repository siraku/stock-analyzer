from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analysis import SignalSnapshot
from app.models.price_cache import PriceCache
from app.models.watchlist import WatchlistTicker
from app.schemas.analysis import SignalSnapshotResponse
from app.schemas.stock import PriceBar, PriceHistoryResponse, TickerInfoResponse
from app.services.price_data import fetch_price_history

router = APIRouter(prefix="/api/v1/stocks", tags=["stocks"])


@router.get("/{ticker}/info", response_model=TickerInfoResponse)
def get_ticker_info(ticker: str, db: Session = Depends(get_db)):
    ticker = ticker.upper()
    obj = db.query(WatchlistTicker).filter(WatchlistTicker.ticker == ticker).first()
    price_row = (
        db.query(PriceCache)
        .filter(PriceCache.ticker == ticker)
        .order_by(PriceCache.date.desc())
        .first()
    )
    return TickerInfoResponse(
        ticker=ticker,
        company_name=obj.company_name if obj else None,
        current_price=price_row.close if price_row else None,
        sector=obj.sector if obj else None,
        market_cap=obj.market_cap if obj else None,
        currency=obj.currency if obj else None,
    )


@router.get("/{ticker}/price-history", response_model=PriceHistoryResponse)
def get_price_history(ticker: str, period: str = "3mo", db: Session = Depends(get_db)):
    ticker = ticker.upper()
    df = fetch_price_history(ticker, db, period=period)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No price data for {ticker}")

    bars = [
        PriceBar(
            date=idx.date(),
            open=row["Open"],
            high=row["High"],
            low=row["Low"],
            close=row["Close"],
            volume=int(row["Volume"]) if row["Volume"] else None,
        )
        for idx, row in df.iterrows()
    ]
    return PriceHistoryResponse(ticker=ticker, bars=bars)


@router.get("/{ticker}/signals", response_model=list[SignalSnapshotResponse])
def get_signal_history(ticker: str, limit: int = 10, db: Session = Depends(get_db)):
    ticker = ticker.upper()
    snapshots = (
        db.query(SignalSnapshot)
        .filter(SignalSnapshot.ticker == ticker)
        .order_by(SignalSnapshot.analyzed_at.desc())
        .limit(limit)
        .all()
    )
    return [SignalSnapshotResponse.from_orm_safe(s) for s in snapshots]
