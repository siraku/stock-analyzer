"""
Enrich stock positions with sector and industry data from yfinance.
Fetches tickers in parallel; caches results in memory for the session.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed

import yfinance as yf

_cache: dict[str, dict] = {}


def enrich_positions(positions: list[dict]) -> list[dict]:
    """
    Add 'sector' and 'industry' to each position dict.
    Parallel-fetches uncached tickers then applies results.
    """
    uncached = [p["ticker"] for p in positions if p["ticker"] not in _cache]
    unique_uncached = list(set(uncached))

    if unique_uncached:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(_fetch_sector, t): t for t in unique_uncached}
            for future in as_completed(futures):
                ticker = futures[future]
                try:
                    _cache[ticker] = future.result()
                except Exception:
                    _cache[ticker] = {"sector": "Unknown", "industry": "Unknown"}

    return [
        {**pos, **_cache.get(pos["ticker"], {"sector": "Unknown", "industry": "Unknown"})}
        for pos in positions
    ]


def _fetch_sector(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info
        sector = info.get("sector") or None
        industry = info.get("industry") or None

        # ETFs have no sector/industry — use fund category as fallback
        if not sector:
            category = info.get("category") or ""
            fund_family = info.get("fundFamily") or ""
            sector = "ETF / Fund"
            industry = category or fund_family or "ETF"

        return {"sector": sector, "industry": industry}
    except Exception:
        return {"sector": "Unknown", "industry": "Unknown"}
