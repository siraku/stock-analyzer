from datetime import datetime
from pydantic import BaseModel, field_validator


class TickerAddRequest(BaseModel):
    ticker: str

    @field_validator("ticker")
    @classmethod
    def uppercase_ticker(cls, v: str) -> str:
        return v.strip().upper()


class TickerUpdateRequest(BaseModel):
    notes: str | None = None


class TickerResponse(BaseModel):
    id: int
    ticker: str
    company_name: str | None
    sector: str | None
    market_cap: float | None
    currency: str | None
    added_at: datetime
    is_active: bool
    notes: str | None

    model_config = {"from_attributes": True}
