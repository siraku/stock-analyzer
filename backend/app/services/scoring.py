"""
Pre-AI scoring logic.
Assigns a numeric score to a SignalSnapshot to decide if AI analysis is needed.
Max score: 150 points.
"""
from app.services.indicators import SignalSnapshot


def score(snap: SignalSnapshot) -> int:
    """Return a score 0-150 based on technical indicator signals."""
    total = 0

    # RSI signals (max 45)
    if snap.rsi_14 is not None:
        if snap.rsi_14 < 30:
            total += 20
        elif snap.rsi_14 < 40:
            total += 8
    if snap.rsi_divergence:
        total += 25

    # MACD signals (max 30)
    if snap.macd_crossover:
        total += 20
    if snap.macd_histogram is not None and snap.macd_histogram > 0:
        # Histogram just turned positive
        total += 10

    # Bollinger Bands (max 25)
    if snap.bb_bounce:
        total += 15
    if snap.price_current and snap.bb_lower and snap.price_current < snap.bb_lower:
        total += 10

    # Volume (max 15)
    if snap.volume_ratio is not None and snap.volume_ratio >= 2.0:
        total += 15
    elif snap.volume_ratio is not None and snap.volume_ratio >= 1.5:
        total += 8

    # Stochastic (max 15)
    if snap.stoch_crossover:
        total += 15
    elif snap.stoch_k is not None and snap.stoch_k < 20:
        total += 5

    # Candlestick pattern (max 10)
    if snap.candle_pattern:
        total += 10

    # Mean reversion context (max 10)
    if snap.price_current and snap.ema50:
        pct_below_ema50 = (snap.ema50 - snap.price_current) / snap.ema50 * 100
        if pct_below_ema50 > 10:
            total += 10
        elif pct_below_ema50 > 5:
            total += 5

    return min(total, 150)


def get_signal_label(score_value: int) -> str:
    """Map numeric score to display label."""
    if score_value >= 70:
        return "high"
    elif score_value >= 40:
        return "medium"
    elif score_value >= 20:
        return "low"
    return "none"
