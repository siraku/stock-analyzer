from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analysis import AnalysisRun, SignalSnapshot
from app.schemas.analysis import (
    AnalysisRunDetailResponse,
    AnalysisRunRequest,
    AnalysisRunSummary,
    SignalSnapshotResponse,
)
from app.services.analysis_runner import run_analysis

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


@router.post("/run", response_model=AnalysisRunDetailResponse)
def trigger_analysis(body: AnalysisRunRequest, db: Session = Depends(get_db)):
    completed_run = run_analysis(db, ticker_list=body.tickers)
    snapshots = (
        db.query(SignalSnapshot)
        .filter(SignalSnapshot.run_id == completed_run.id)
        .order_by(SignalSnapshot.pre_score.desc())
        .all()
    )
    return AnalysisRunDetailResponse(
        run=AnalysisRunSummary.model_validate(completed_run),
        results=[SignalSnapshotResponse.from_orm_safe(s) for s in snapshots],
    )


@router.get("/runs", response_model=list[AnalysisRunSummary])
def list_runs(limit: int = 20, db: Session = Depends(get_db)):
    return (
        db.query(AnalysisRun)
        .order_by(AnalysisRun.run_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/runs/{run_id}", response_model=AnalysisRunDetailResponse)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    snapshots = (
        db.query(SignalSnapshot)
        .filter(SignalSnapshot.run_id == run_id)
        .order_by(SignalSnapshot.pre_score.desc())
        .all()
    )
    return AnalysisRunDetailResponse(
        run=AnalysisRunSummary.model_validate(run),
        results=[SignalSnapshotResponse.from_orm_safe(s) for s in snapshots],
    )


@router.get("/latest", response_model=AnalysisRunDetailResponse | None)
def get_latest(db: Session = Depends(get_db)):
    run = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.status == "complete")
        .order_by(AnalysisRun.run_at.desc())
        .first()
    )
    if not run:
        return None
    snapshots = (
        db.query(SignalSnapshot)
        .filter(SignalSnapshot.run_id == run.id)
        .order_by(SignalSnapshot.pre_score.desc())
        .all()
    )
    return AnalysisRunDetailResponse(
        run=AnalysisRunSummary.model_validate(run),
        results=[SignalSnapshotResponse.from_orm_safe(s) for s in snapshots],
    )
