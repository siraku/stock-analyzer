import yfinance as yf


def validate_and_fetch_info(ticker: str) -> dict | None:
    """
    Validate that a ticker exists on Yahoo Finance and return basic info.
    Supports any market: US (AAPL), Japan (7203.T), HK (0700.HK), etc.
    Returns None if the ticker is invalid or not found.
    """
    ticker = ticker.strip().upper()
    try:
        info = yf.Ticker(ticker).info
        # yfinance returns a minimal dict for invalid tickers
        if not info.get("regularMarketPrice") and not info.get("currentPrice") and not info.get("previousClose"):
            return None
        return {
            "ticker": ticker,
            "company_name": info.get("longName") or info.get("shortName", ticker),
            "sector": info.get("sector"),
            "market_cap": info.get("marketCap"),
            "currency": info.get("currency"),
        }
    except Exception:
        return None
