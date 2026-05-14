from datetime import date, datetime
from sqlalchemy import Date, DateTime, Float, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PriceCache(Base):
    __tablename__ = "price_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    price_date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    close: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[int | None] = mapped_column(Integer)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("ticker", "price_date", name="uq_price_ticker_date"),
        Index("idx_price_cache_ticker_date", "ticker", "price_date"),
    )
