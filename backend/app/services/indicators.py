"""
Technical indicator computation.
All functions operate on a pandas DataFrame with columns:
  Open, High, Low, Close, Volume  (DatetimeIndex)
"""
from dataclasses import dataclass, field

import pandas as pd
import pandas_ta as ta


@dataclass
class SignalSnapshot:
    ticker: str
    price_current: float | None = None

    # RSI
    rsi_14: float | None = None
    rsi_divergence: bool = False

    # MACD
    macd_value: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    macd_crossover: bool = False

    # Moving averages
    ema20: float | None = None
    ema50: float | None = None

    # Bollinger Bands
    bb_upper: float | None = None
    bb_middle: float | None = None
    bb_lower: float | None = None
    bb_bounce: bool = False

    # Volume
    volume_ratio: float | None = None

    # Stochastic
    stoch_k: float | None = None
    stoch_d: float | None = None
    stoch_crossover: bool = False

    # Candlestick patterns
    candle_pattern: str | None = None

    # Extra context
    price_52w_high: float | None = None
    price_52w_low: float | None = None


def compute(df: pd.DataFrame, ticker: str) -> SignalSnapshot:
    """
    Compute all technical indicators from OHLCV DataFrame.
    Returns a populated SignalSnapshot.
    """
    snap = SignalSnapshot(ticker=ticker)

    if df.empty or len(df) < 30:
        return snap

    snap.price_current = float(df["Close"].iloc[-1])
    snap.price_52w_high = float(df["High"].tail(252).max())
    snap.price_52w_low = float(df["Low"].tail(252).min())

    _compute_rsi(df, snap)
    _compute_macd(df, snap)
    _compute_ema(df, snap)
    _compute_bollinger(df, snap)
    _compute_volume(df, snap)
    _compute_stochastic(df, snap)
    _compute_candle_patterns(df, snap)

    return snap


# ── RSI ──────────────────────────────────────────────────────────────────────

def _compute_rsi(df: pd.DataFrame, snap: SignalSnapshot) -> None:
    rsi_series = ta.rsi(df["Close"], length=14)
    if rsi_series is None or rsi_series.dropna().empty:
        return

    snap.rsi_14 = round(float(rsi_series.iloc[-1]), 2)

    # Bullish divergence: price makes lower low, RSI makes higher low (last 5 candles)
    if len(rsi_series.dropna()) >= 5:
        recent_close = df["Close"].iloc[-5:]
        recent_rsi = rsi_series.iloc[-5:]
        price_lower_low = recent_close.iloc[-1] < recent_close.min()
        rsi_higher_low = recent_rsi.iloc[-1] > recent_rsi.min()
        snap.rsi_divergence = bool(price_lower_low and rsi_higher_low and snap.rsi_14 < 40)


# ── MACD ─────────────────────────────────────────────────────────────────────

def _compute_macd(df: pd.DataFrame, snap: SignalSnapshot) -> None:
    macd_df = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    if macd_df is None or macd_df.empty:
        return

    macd_col = [c for c in macd_df.columns if "MACD_" in c and "MACDs" not in c and "MACDh" not in c]
    signal_col = [c for c in macd_df.columns if "MACDs_" in c]
    hist_col = [c for c in macd_df.columns if "MACDh_" in c]

    if not (macd_col and signal_col and hist_col):
        return

    snap.macd_value = round(float(macd_df[macd_col[0]].iloc[-1]), 4)
    snap.macd_signal = round(float(macd_df[signal_col[0]].iloc[-1]), 4)
    snap.macd_histogram = round(float(macd_df[hist_col[0]].iloc[-1]), 4)

    # Bullish crossover: MACD crossed above signal line in last 3 candles
    hist = macd_df[hist_col[0]].dropna()
    if len(hist) >= 3:
        prev_hist = hist.iloc[-3:-1]
        curr_hist = hist.iloc[-1]
        snap.macd_crossover = bool(curr_hist > 0 and any(v < 0 for v in prev_hist))


# ── EMA ──────────────────────────────────────────────────────────────────────

def _compute_ema(df: pd.DataFrame, snap: SignalSnapshot) -> None:
    ema20 = ta.ema(df["Close"], length=20)
    ema50 = ta.ema(df["Close"], length=50)

    if ema20 is not None and not ema20.dropna().empty:
        snap.ema20 = round(float(ema20.iloc[-1]), 2)
    if ema50 is not None and not ema50.dropna().empty:
        snap.ema50 = round(float(ema50.iloc[-1]), 2)


# ── Bollinger Bands ───────────────────────────────────────────────────────────

def _compute_bollinger(df: pd.DataFrame, snap: SignalSnapshot) -> None:
    bb = ta.bbands(df["Close"], length=20, std=2)
    if bb is None or bb.empty:
        return

    upper_col = [c for c in bb.columns if "BBU_" in c]
    mid_col = [c for c in bb.columns if "BBM_" in c]
    lower_col = [c for c in bb.columns if "BBL_" in c]

    if not (upper_col and mid_col and lower_col):
        return

    snap.bb_upper = round(float(bb[upper_col[0]].iloc[-1]), 2)
    snap.bb_middle = round(float(bb[mid_col[0]].iloc[-1]), 2)
    snap.bb_lower = round(float(bb[lower_col[0]].iloc[-1]), 2)

    # Bollinger bounce: previous close was at or below lower band, current close is back inside
    if len(df) >= 2:
        prev_close = float(df["Close"].iloc[-2])
        prev_lower = float(bb[lower_col[0]].iloc[-2])
        curr_close = float(df["Close"].iloc[-1])
        curr_lower = float(bb[lower_col[0]].iloc[-1])
        snap.bb_bounce = bool(prev_close <= prev_lower and curr_close > curr_lower)


# ── Volume ────────────────────────────────────────────────────────────────────

def _compute_volume(df: pd.DataFrame, snap: SignalSnapshot) -> None:
    if "Volume" not in df.columns or len(df) < 21:
        return
    avg_vol = df["Volume"].iloc[-21:-1].mean()
    curr_vol = float(df["Volume"].iloc[-1])
    if avg_vol > 0:
        snap.volume_ratio = round(curr_vol / avg_vol, 2)


# ── Stochastic ────────────────────────────────────────────────────────────────

def _compute_stochastic(df: pd.DataFrame, snap: SignalSnapshot) -> None:
    stoch = ta.stoch(df["High"], df["Low"], df["Close"], k=14, d=3, smooth_k=3)
    if stoch is None or stoch.empty:
        return

    k_col = [c for c in stoch.columns if "STOCHk_" in c]
    d_col = [c for c in stoch.columns if "STOCHd_" in c]

    if not (k_col and d_col):
        return

    snap.stoch_k = round(float(stoch[k_col[0]].iloc[-1]), 2)
    snap.stoch_d = round(float(stoch[d_col[0]].iloc[-1]), 2)

    # Bullish crossover in oversold zone: %K crossed above %D, both below 20
    if len(stoch) >= 2:
        prev_k = float(stoch[k_col[0]].iloc[-2])
        prev_d = float(stoch[d_col[0]].iloc[-2])
        snap.stoch_crossover = bool(
            snap.stoch_k < 30
            and snap.stoch_d < 30
            and prev_k < prev_d
            and snap.stoch_k >= snap.stoch_d
        )


# ── Candlestick Patterns ──────────────────────────────────────────────────────

_BULLISH_PATTERNS = [
    "CDL_HAMMER",
    "CDL_INVERTEDHAMMER",
    "CDL_MORNINGSTAR",
    "CDL_ENGULFING",
    "CDL_DOJI_10_0.1",
    "CDL_DRAGONFLYDOJI",
]


def _compute_candle_patterns(df: pd.DataFrame, snap: SignalSnapshot) -> None:
    if len(df) < 5:
        return

    detected = []
    for pattern in _BULLISH_PATTERNS:
        try:
            result = df.ta(kind=pattern)
            if result is not None and not result.empty:
                val = result.iloc[-1]
                if val > 0:
                    detected.append(pattern.replace("CDL_", "").split("_")[0].title())
        except Exception:
            continue

    snap.candle_pattern = detected[0] if detected else None
