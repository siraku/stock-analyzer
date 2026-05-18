"""
Fetches fundamental financial data for a ticker via yfinance.
Provides business context (revenue trend, margins, sentiment) for the AI interpreter.
Results are cached in memory for 24 hours — fundamentals change quarterly, not daily.
"""
from __future__ import annotations

import math
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import yfinance as yf


@dataclass
class FundamentalSnapshot:
    ticker: str
    sector: str | None = None
    industry: str | None = None
    # Revenue trend: oldest → newest, in USD millions
    revenue_trend_m: list[float] = field(default_factory=list)
    revenue_change_pct: float | None = None        # % change from oldest to newest quarter in window
    # Margins
    gross_margin_pct: float | None = None          # latest quarter
    gross_margin_direction: str | None = None      # "improving" | "deteriorating" | "stable"
    # R&D intensity
    rd_pct_of_revenue: float | None = None         # latest quarter R&D / revenue
    # Operating profitability trend: oldest → newest, in USD millions
    operating_income_trend_m: list[float] = field(default_factory=list)
    # Balance sheet
    debt_to_equity: float | None = None
    # Market sentiment
    short_float_pct: float | None = None           # % of float sold short
    analyst_recommendation: str | None = None      # "Strong Buy" | "Buy" | "Hold" | "Underperform" | "Sell"
    # Earnings
    next_earnings_date: str | None = None
    last_earnings_surprise_pct: float | None = None  # positive = beat, negative = miss


# In-memory cache: ticker → (snapshot, fetched_at)
_cache: dict[str, tuple[FundamentalSnapshot, datetime]] = {}
_cache_lock = threading.Lock()
_CACHE_TTL = timedelta(hours=24)


def fetch_fundamentals(ticker: str) -> FundamentalSnapshot | None:
    """
    Return a FundamentalSnapshot for the ticker.
    Returns None if data is unavailable — never raises.
    """
    ticker = ticker.upper()

    with _cache_lock:
        if ticker in _cache:
            snap, fetched_at = _cache[ticker]
            if datetime.utcnow() - fetched_at < _CACHE_TTL:
                return snap

    try:
        snap = _fetch(ticker)
    except Exception as exc:
        print(f"[fundamental_data] Failed for {ticker}: {exc}")
        return None

    with _cache_lock:
        _cache[ticker] = (snap, datetime.utcnow())

    return snap


def format_for_prompt(snap: FundamentalSnapshot) -> str:
    """
    Render a FundamentalSnapshot as a plain-text block suitable for injection
    into the AI prompt.
    """
    lines = ["FUNDAMENTAL CONTEXT:"]

    if snap.sector or snap.industry:
        lines.append(f"Sector/Industry: {snap.sector or '?'} / {snap.industry or '?'}")

    if snap.revenue_trend_m:
        rev_str = " → ".join(f"${v}M" for v in snap.revenue_trend_m)
        lines.append(f"Revenue (last {len(snap.revenue_trend_m)}Q, oldest→newest): {rev_str}")
    if snap.revenue_change_pct is not None:
        lines.append(f"Revenue change over window: {snap.revenue_change_pct:+.1f}%")

    if snap.gross_margin_pct is not None:
        direction = f" — {snap.gross_margin_direction}" if snap.gross_margin_direction else ""
        lines.append(f"Gross margin (latest Q): {snap.gross_margin_pct}%{direction}")

    if snap.rd_pct_of_revenue is not None:
        lines.append(f"R&D as % of revenue: {snap.rd_pct_of_revenue}%")

    if snap.operating_income_trend_m:
        op_str = " → ".join(f"${v}M" for v in snap.operating_income_trend_m)
        lines.append(f"Operating income (last {len(snap.operating_income_trend_m)}Q): {op_str}")

    if snap.debt_to_equity is not None:
        lines.append(f"Debt/Equity: {snap.debt_to_equity:.2f}x")

    if snap.short_float_pct is not None:
        lines.append(f"Short interest: {snap.short_float_pct:.1f}% of float")

    if snap.analyst_recommendation:
        lines.append(f"Analyst consensus: {snap.analyst_recommendation}")

    if snap.next_earnings_date:
        lines.append(f"Next earnings: {snap.next_earnings_date}")

    if snap.last_earnings_surprise_pct is not None:
        lines.append(f"Last earnings surprise: {snap.last_earnings_surprise_pct:+.1f}%")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fetch(ticker: str) -> FundamentalSnapshot:
    t = yf.Ticker(ticker)
    info = t.info or {}
    snap = FundamentalSnapshot(ticker=ticker)

    snap.sector = info.get("sector") or None
    snap.industry = info.get("industry") or None

    # --- Quarterly income statement ---
    # yfinance exposes this as .quarterly_financials (older) or .quarterly_income_stmt (newer)
    qf = None
    for attr in ("quarterly_income_stmt", "quarterly_financials"):
        try:
            qf = getattr(t, attr, None)
            if qf is not None and not qf.empty:
                break
        except Exception:
            continue

    if qf is not None and not qf.empty:
        _parse_income_statement(snap, qf)

    # --- Balance sheet ---
    raw_de = info.get("debtToEquity")
    if _valid(raw_de):
        # yfinance returns D/E as a percentage-style number (e.g. 85.4 = 0.854x)
        snap.debt_to_equity = round(float(raw_de) / 100, 2)

    # --- Market sentiment ---
    short_pct = info.get("shortPercentOfFloat")
    if _valid(short_pct) and isinstance(short_pct, (int, float)):
        # yfinance returns as a decimal (0.15 = 15%)
        snap.short_float_pct = round(float(short_pct) * 100, 1) if float(short_pct) <= 1.0 else round(float(short_pct), 1)

    snap.analyst_recommendation = _normalize_rec(info.get("recommendationKey", ""))

    # --- Earnings ---
    try:
        ed = t.earnings_dates
        if ed is not None and not ed.empty:
            now = datetime.utcnow()
            # Next earnings: earliest future date
            future = ed[ed.index.tz_localize(None) > now] if ed.index.tz is not None else ed[ed.index > now]
            if not future.empty:
                snap.next_earnings_date = future.index[-1].strftime("%Y-%m-%d")
            # Last surprise: most recent past date with a non-null surprise
            past = ed[ed.index.tz_localize(None) <= now] if ed.index.tz is not None else ed[ed.index <= now]
            surprise_col = next((c for c in past.columns if "surprise" in c.lower()), None)
            if surprise_col:
                past_valid = past.dropna(subset=[surprise_col])
                if not past_valid.empty:
                    snap.last_earnings_surprise_pct = round(float(past_valid.iloc[0][surprise_col]), 1)
    except Exception:
        pass

    return snap


def _parse_income_statement(snap: FundamentalSnapshot, qf) -> None:
    """Extract revenue, margins, R&D, and operating income from quarterly financials DataFrame."""
    # Use only the 4 most recent quarters
    cols = list(qf.columns[:4])

    rev_row = _find_row(qf, ["Total Revenue", "Revenue"])
    gp_row  = _find_row(qf, ["Gross Profit"])
    rd_row  = _find_row(qf, ["Research And Development", "Research Development", "ResearchAndDevelopment"])
    op_row  = _find_row(qf, ["Operating Income", "EBIT", "Total Operating Income As Reported"])

    # Revenue trend (oldest → newest)
    if rev_row:
        rev_vals = [_get(qf, rev_row, c) for c in cols]
        rev_valid = [round(v / 1e6, 1) for v in rev_vals if v is not None]
        snap.revenue_trend_m = list(reversed(rev_valid))  # oldest first
        if len(rev_valid) >= 2:
            newest, oldest = rev_valid[0], rev_valid[-1]
            if oldest and oldest != 0:
                snap.revenue_change_pct = round((newest - oldest) / abs(oldest) * 100, 1)

    # Gross margin (latest Q, and direction vs previous Q)
    if gp_row and rev_row:
        gp_curr = _get(qf, gp_row, cols[0])
        rv_curr = _get(qf, rev_row, cols[0])
        gp_prev = _get(qf, gp_row, cols[1]) if len(cols) > 1 else None
        rv_prev = _get(qf, rev_row, cols[1]) if len(cols) > 1 else None

        if gp_curr is not None and rv_curr and rv_curr != 0:
            snap.gross_margin_pct = round(gp_curr / rv_curr * 100, 1)

        if all(v is not None and v != 0 for v in [gp_curr, rv_curr, gp_prev, rv_prev]):
            diff = (gp_curr / rv_curr) - (gp_prev / rv_prev)
            snap.gross_margin_direction = (
                "improving"     if diff >  0.02 else
                "deteriorating" if diff < -0.02 else
                "stable"
            )

    # R&D as % of revenue (latest Q)
    if rd_row and rev_row:
        rd_val = _get(qf, rd_row, cols[0])
        rv_val = _get(qf, rev_row, cols[0])
        if rd_val is not None and rv_val and rv_val != 0:
            snap.rd_pct_of_revenue = round(abs(rd_val) / rv_val * 100, 1)

    # Operating income trend (oldest → newest)
    if op_row:
        op_vals = [_get(qf, op_row, c) for c in cols]
        op_valid = [round(v / 1e6, 1) for v in op_vals if v is not None]
        snap.operating_income_trend_m = list(reversed(op_valid))


def _find_row(df, candidates: list[str]):
    """Find a row index by exact match, then partial match."""
    for name in candidates:
        if name in df.index:
            return name
    for name in candidates:
        matches = [idx for idx in df.index if name.lower() in str(idx).lower()]
        if matches:
            return matches[0]
    return None


def _get(df, row, col):
    """Return df.loc[row, col] as float, or None if missing/NaN."""
    try:
        v = df.loc[row, col]
        return None if not _valid(v) else float(v)
    except Exception:
        return None


def _valid(v) -> bool:
    if v is None:
        return False
    try:
        return not math.isnan(float(v))
    except (TypeError, ValueError):
        return False


def _normalize_rec(key: str) -> str | None:
    return {
        "strongbuy":    "Strong Buy",
        "strong_buy":   "Strong Buy",
        "buy":          "Buy",
        "hold":         "Hold",
        "underperform": "Underperform",
        "sell":         "Sell",
        "strongsell":   "Sell",
        "strong_sell":  "Sell",
    }.get(key.lower().replace(" ", "") if key else "", None)
