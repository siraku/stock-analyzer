from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.watchlist import WatchlistTicker
from app.schemas.watchlist import TickerAddRequest, TickerResponse, TickerUpdateRequest
from app.utils.ticker_validator import validate_and_fetch_info

router = APIRouter(prefix="/api/v1/watchlist", tags=["watchlist"])


@router.get("", response_model=list[TickerResponse])
def list_tickers(db: Session = Depends(get_db)):
    return db.query(WatchlistTicker).filter(WatchlistTicker.is_active == True).all()


@router.post("", response_model=TickerResponse, status_code=201)
def add_ticker(body: TickerAddRequest, db: Session = Depends(get_db)):
    existing = db.query(WatchlistTicker).filter(WatchlistTicker.ticker == body.ticker).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(status_code=409, detail=f"{body.ticker} is already in watchlist")

    info = validate_and_fetch_info(body.ticker)
    if info is None:
        raise HTTPException(status_code=404, detail=f"Ticker {body.ticker} not found on Yahoo Finance")

    ticker = WatchlistTicker(
        ticker=info["ticker"],
        company_name=info["company_name"],
        sector=info["sector"],
        market_cap=info["market_cap"],
        currency=info.get("currency"),
    )
    db.add(ticker)
    db.commit()
    db.refresh(ticker)
    return ticker


@router.delete("/{ticker}", status_code=204)
def remove_ticker(ticker: str, db: Session = Depends(get_db)):
    obj = db.query(WatchlistTicker).filter(WatchlistTicker.ticker == ticker.upper()).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Ticker not found")
    obj.is_active = False
    db.commit()


@router.patch("/{ticker}", response_model=TickerResponse)
def update_ticker(ticker: str, body: TickerUpdateRequest, db: Session = Depends(get_db)):
    obj = db.query(WatchlistTicker).filter(WatchlistTicker.ticker == ticker.upper()).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Ticker not found")
    if body.notes is not None:
        obj.notes = body.notes
    db.commit()
    db.refresh(obj)
    return obj
