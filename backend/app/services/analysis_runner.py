"""
Orchestrates the full analysis pipeline for a list of tickers.
"""
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.analysis import AnalysisRun, SignalSnapshot as SignalSnapshotModel
from app.models.watchlist import WatchlistTicker
from app.services import ai_interpreter, indicators, scoring
from app.services.price_data import fetch_price_history


def run_analysis(db: Session, ticker_list: list[str] | None = None) -> AnalysisRun:
    """
    Run full analysis pipeline.
    If ticker_list is None, uses all active watchlist tickers.
    Returns the completed AnalysisRun ORM object.
    """
    # Resolve ticker list
    if ticker_list is None:
        tickers = [
            t.ticker
            for t in db.query(WatchlistTicker).filter(WatchlistTicker.is_active == True).all()
        ]
    else:
        tickers = [t.upper() for t in ticker_list]

    # Create run record
    run = AnalysisRun(status="running", tickers_analyzed=0, tickers_signaled=0)
    db.add(run)
    db.commit()
    db.refresh(run)

    start_ts = time.time()
    signaled = 0

    for ticker in tickers:
        try:
            snapshot = _analyze_ticker(ticker, db, run.id)
            if snapshot:
                db.add(snapshot)
                if snapshot.reversal_likelihood in ("high", "medium"):
                    signaled += 1
        except Exception as exc:
            # Log and continue — one bad ticker shouldn't abort the whole run
            print(f"[analysis_runner] Error analyzing {ticker}: {exc}")
            continue

    # Finalize run
    elapsed_ms = int((time.time() - start_ts) * 1000)
    run.status = "complete"
    run.tickers_analyzed = len(tickers)
    run.tickers_signaled = signaled
    run.duration_ms = elapsed_ms
    db.commit()
    db.refresh(run)

    return run


def _analyze_ticker(ticker: str, db: Session, run_id: int) -> SignalSnapshotModel | None:
    df = fetch_price_history(ticker, db)
    if df.empty:
        return None

    snap = indicators.compute(df, ticker)
    score_value = scoring.score(snap)

    # Only call AI for stocks above threshold
    if score_value >= settings.analysis_score_threshold:
        ai_result = ai_interpreter.interpret(snap, score_value)
    else:
        ai_result = {
            "reversal_likelihood": scoring.get_signal_label(score_value),
            "confidence": 0,
            "key_signals": [],
            "risk_factors": [],
            "summary": "Score below threshold — skipped AI analysis.",
            "tokens_used": 0,
        }

    import json

    return SignalSnapshotModel(
        run_id=run_id,
        ticker=ticker,
        analyzed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        # Indicator values
        rsi_14=snap.rsi_14,
        rsi_divergence=snap.rsi_divergence,
        macd_value=snap.macd_value,
        macd_signal=snap.macd_signal,
        macd_histogram=snap.macd_histogram,
        macd_crossover=snap.macd_crossover,
        ema20=snap.ema20,
        ema50=snap.ema50,
        bb_upper=snap.bb_upper,
        bb_lower=snap.bb_lower,
        bb_middle=snap.bb_middle,
        bb_bounce=snap.bb_bounce,
        volume_ratio=snap.volume_ratio,
        stoch_k=snap.stoch_k,
        stoch_d=snap.stoch_d,
        stoch_crossover=snap.stoch_crossover,
        candle_pattern=snap.candle_pattern,
        price_current=snap.price_current,
        pre_score=score_value,
        # AI results
        reversal_likelihood=ai_result.get("reversal_likelihood"),
        ai_confidence=ai_result.get("confidence"),
        ai_key_signals=json.dumps(ai_result.get("key_signals", []), ensure_ascii=False),
        ai_risk_factors=json.dumps(ai_result.get("risk_factors", []), ensure_ascii=False),
        ai_summary=ai_result.get("summary"),
        ai_tokens_used=ai_result.get("tokens_used", 0),
    )
