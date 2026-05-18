"""
Portfolio analysis router.
Uses AI-generated thematic groups stored in the ticker_groups DB table.
"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ticker_group import TickerGroup
from app.services.group_classifier import classify_tickers
from app.services.portfolio_parser import parse_portfolio_csv

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])


# ── Request/response models ────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    file_path: str


class RenameGroupRequest(BaseModel):
    old_name: str
    new_name: str


class ReassignRequest(BaseModel):
    group_name: str


# ── Helpers ────────────────────────────────────────────────────────────────────

def _resolve_csv_path(file_path: str) -> str:
    """If file_path is a directory, find the most recent assetbalance CSV inside it."""
    p = Path(file_path)
    if p.is_dir():
        csvs = sorted(p.glob("assetbalance*.csv"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not csvs:
            raise FileNotFoundError(f"No assetbalance*.csv found in {file_path}")
        return str(csvs[0])
    return file_path


def _build_response(positions: list[dict]) -> dict:
    group_map: dict[str, list[dict]] = {}
    for pos in positions:
        group_map.setdefault(pos["group_name"], []).append(pos)

    total_value = sum(p["current_value_jpy"] for p in positions)
    total_pnl = sum(p["pnl_jpy"] for p in positions)
    total_cost = total_value - total_pnl

    groups = []
    for group_name, grp_positions in sorted(
        group_map.items(), key=lambda x: -sum(p["current_value_jpy"] for p in x[1])
    ):
        grp_value = sum(p["current_value_jpy"] for p in grp_positions)
        grp_pnl = sum(p["pnl_jpy"] for p in grp_positions)
        grp_cost = grp_value - grp_pnl
        groups.append({
            "group_name": group_name,
            "positions": grp_positions,
            "total_value_jpy": grp_value,
            "total_pnl_jpy": grp_pnl,
            "pnl_pct": round(grp_pnl / grp_cost * 100, 2) if grp_cost else 0.0,
            "value_pct": round(grp_value / total_value * 100, 1) if total_value else 0.0,
            "position_count": len(grp_positions),
        })

    return {
        "groups": groups,
        "total_value_jpy": total_value,
        "total_pnl_jpy": total_pnl,
        "pnl_pct": round(total_pnl / total_cost * 100, 2) if total_cost else 0.0,
        "position_count": len(positions),
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/analyze")
def analyze_portfolio(body: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Parse a Rakuten Securities portfolio CSV, assign thematic groups (AI-classified
    on first run, DB-cached thereafter), and return a group-breakdown of US stock positions.
    """
    try:
        resolved = _resolve_csv_path(body.file_path)
        positions = parse_portfolio_csv(resolved)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not positions:
        raise HTTPException(status_code=422, detail="No US stock positions found in CSV")

    tickers = [p["ticker"] for p in positions]

    # Load existing group assignments from DB
    existing: dict[str, str] = {
        row.ticker: row.group_name
        for row in db.query(TickerGroup).filter(TickerGroup.ticker.in_(tickers)).all()
    }

    # Classify any tickers not yet in DB
    new_positions = [p for p in positions if p["ticker"] not in existing]
    if new_positions:
        classified = classify_tickers(new_positions)
        for p in new_positions:
            ticker = p["ticker"]
            group_name = classified.get(ticker, "Uncategorized")
            db.add(TickerGroup(ticker=ticker, group_name=group_name))
            existing[ticker] = group_name
        db.commit()

    # Attach group_name to each position
    for p in positions:
        p["group_name"] = existing.get(p["ticker"], "Uncategorized")

    return _build_response(positions)


@router.get("/groups")
def get_groups(db: Session = Depends(get_db)):
    """Return all saved ticker → group_name assignments."""
    rows = db.query(TickerGroup).all()
    return {row.ticker: row.group_name for row in rows}


@router.patch("/groups/rename")
def rename_group(body: RenameGroupRequest, db: Session = Depends(get_db)):
    """Rename a group — updates every ticker assigned to old_name."""
    if not body.new_name.strip():
        raise HTTPException(status_code=422, detail="new_name must not be empty")
    updated = (
        db.query(TickerGroup)
        .filter(TickerGroup.group_name == body.old_name)
        .update({"group_name": body.new_name.strip()})
    )
    db.commit()
    return {"ok": True, "updated": updated}


@router.patch("/groups/{ticker}")
def reassign_ticker(ticker: str, body: ReassignRequest, db: Session = Depends(get_db)):
    """Reassign a single ticker to a different (or new) group."""
    if not body.group_name.strip():
        raise HTTPException(status_code=422, detail="group_name must not be empty")
    row = db.query(TickerGroup).filter(TickerGroup.ticker == ticker.upper()).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found in group assignments")
    row.group_name = body.group_name.strip()
    db.commit()
    return {"ok": True}
