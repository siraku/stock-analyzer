from datetime import date
from pydantic import BaseModel


class PriceBar(BaseModel):
    date: date
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: int | None


class PriceHistoryResponse(BaseModel):
    ticker: str
    bars: list[PriceBar]


class TickerInfoResponse(BaseModel):
    ticker: str
    company_name: str | None
    current_price: float | None
    sector: str | None
    market_cap: float | None
    currency: str | None
