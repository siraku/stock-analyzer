"""
Parse Rakuten Securities asset balance CSV (CP932 encoding).
Extracts US stock rows and returns structured position data.
"""
import csv
import io
from pathlib import Path


def parse_portfolio_csv(file_path: str) -> list[dict]:
    """
    Parse a Rakuten Securities asset balance CSV.
    Returns a list of US stock position dicts.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, encoding="cp932") as f:
        content = f.read()

    reader = csv.reader(io.StringIO(content))
    rows = list(reader)

    # Locate the detail section header: 種別,銘柄コード・ティッカー,...
    header_idx = None
    for i, row in enumerate(rows):
        if row and row[0] == "種別":
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("Could not find holdings detail section in CSV")

    positions = []
    for row in rows[header_idx + 1:]:
        if not row or not row[0]:
            continue
        if row[0] != "米国株式":  # US stocks only
            continue

        try:
            ticker = row[1].strip()
            company_name = row[2].strip()
            account = row[3].strip()
            quantity = _parse_float(row[4])
            avg_cost = _parse_float(row[6])
            cost_currency = row[7].strip()
            current_price = _parse_float(row[8])
            current_value_jpy = _parse_float(row[14])
            pnl_jpy = _parse_float(row[16])
            pnl_pct = _parse_float(row[17])
        except (IndexError, ValueError):
            continue

        if not ticker:
            continue

        positions.append({
            "ticker": ticker,
            "company_name": company_name,
            "account": account,
            "quantity": quantity,
            "avg_cost": avg_cost,
            "cost_currency": cost_currency,
            "current_price": current_price,
            "current_value_jpy": current_value_jpy,
            "pnl_jpy": pnl_jpy,
            "pnl_pct": pnl_pct,
        })

    return positions


def _parse_float(value: str) -> float:
    try:
        return float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0
