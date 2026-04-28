import json
from datetime import datetime
from pydantic import BaseModel, model_validator


class AnalysisRunRequest(BaseModel):
    tickers: list[str] | None = None


class AnalysisRunSummary(BaseModel):
    id: int
    run_at: datetime
    status: str
    tickers_analyzed: int | None
    tickers_signaled: int | None
    duration_ms: int | None

    model_config = {"from_attributes": True}


class SignalSnapshotResponse(BaseModel):
    id: int
    ticker: str
    analyzed_at: datetime
    price_current: float | None
    rsi_14: float | None
    rsi_divergence: bool | None
    macd_value: float | None
    macd_signal: float | None
    macd_histogram: float | None
    macd_crossover: bool | None
    ema20: float | None
    ema50: float | None
    bb_upper: float | None
    bb_middle: float | None
    bb_lower: float | None
    bb_bounce: bool | None
    volume_ratio: float | None
    stoch_k: float | None
    stoch_d: float | None
    stoch_crossover: bool | None
    candle_pattern: str | None
    pre_score: int | None
    reversal_likelihood: str | None
    ai_confidence: int | None
    ai_key_signals: list[str] | None
    ai_risk_factors: list[str] | None
    ai_summary: str | None
    ai_tokens_used: int | None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_json_fields(cls, values):
        # ORM objects come in as attribute access, not dict
        if hasattr(values, "__dict__"):
            obj = values
            raw_signals = getattr(obj, "ai_key_signals", None)
            raw_risks = getattr(obj, "ai_risk_factors", None)
            # We'll handle JSON parsing in the response model itself
            return values
        # Dict path
        for field in ("ai_key_signals", "ai_risk_factors"):
            val = values.get(field)
            if isinstance(val, str):
                try:
                    values[field] = json.loads(val)
                except Exception:
                    values[field] = []
        return values

    @classmethod
    def from_orm_safe(cls, obj) -> "SignalSnapshotResponse":
        """Parse JSON string fields from ORM object."""
        data = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        for field in ("ai_key_signals", "ai_risk_factors"):
            val = data.get(field)
            if isinstance(val, str):
                try:
                    data[field] = json.loads(val)
                except Exception:
                    data[field] = []
        return cls(**data)


class AnalysisRunDetailResponse(BaseModel):
    run: AnalysisRunSummary
    results: list[SignalSnapshotResponse]
