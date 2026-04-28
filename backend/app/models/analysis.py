from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    status: Mapped[str] = mapped_column(String(20), default="pending")
    tickers_analyzed: Mapped[int | None] = mapped_column(Integer)
    tickers_signaled: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    snapshots: Mapped[list["SignalSnapshot"]] = relationship(
        "SignalSnapshot", back_populates="run", cascade="all, delete-orphan"
    )


class SignalSnapshot(Base):
    __tablename__ = "signal_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("analysis_runs.id"))
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Raw indicator values
    rsi_14: Mapped[float | None] = mapped_column(Float)
    rsi_divergence: Mapped[bool | None] = mapped_column(Boolean)
    macd_value: Mapped[float | None] = mapped_column(Float)
    macd_signal: Mapped[float | None] = mapped_column(Float)
    macd_histogram: Mapped[float | None] = mapped_column(Float)
    macd_crossover: Mapped[bool | None] = mapped_column(Boolean)
    ema20: Mapped[float | None] = mapped_column(Float)
    ema50: Mapped[float | None] = mapped_column(Float)
    bb_upper: Mapped[float | None] = mapped_column(Float)
    bb_lower: Mapped[float | None] = mapped_column(Float)
    bb_middle: Mapped[float | None] = mapped_column(Float)
    bb_bounce: Mapped[bool | None] = mapped_column(Boolean)
    volume_ratio: Mapped[float | None] = mapped_column(Float)
    stoch_k: Mapped[float | None] = mapped_column(Float)
    stoch_d: Mapped[float | None] = mapped_column(Float)
    stoch_crossover: Mapped[bool | None] = mapped_column(Boolean)
    candle_pattern: Mapped[str | None] = mapped_column(String(100))
    price_current: Mapped[float | None] = mapped_column(Float)
    pre_score: Mapped[int | None] = mapped_column(Integer)

    # AI output
    reversal_likelihood: Mapped[str | None] = mapped_column(String(20))
    ai_confidence: Mapped[int | None] = mapped_column(Integer)
    ai_key_signals: Mapped[str | None] = mapped_column(Text)   # JSON array as text
    ai_risk_factors: Mapped[str | None] = mapped_column(Text)  # JSON array as text
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_tokens_used: Mapped[int | None] = mapped_column(Integer)

    run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="snapshots")

    __table_args__ = (
        Index("idx_snapshots_ticker", "ticker"),
        Index("idx_snapshots_run", "run_id"),
    )
