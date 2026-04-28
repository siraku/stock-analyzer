from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings as app_settings
from app.database import get_db

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    claude_api_key_set: bool
    analysis_score_threshold: int
    price_cache_ttl_minutes: int


class SettingsUpdateRequest(BaseModel):
    claude_api_key: str | None = None
    analysis_score_threshold: int | None = None


@router.get("", response_model=SettingsResponse)
def get_settings():
    return SettingsResponse(
        claude_api_key_set=bool(app_settings.claude_api_key),
        analysis_score_threshold=app_settings.analysis_score_threshold,
        price_cache_ttl_minutes=app_settings.price_cache_ttl_minutes,
    )


@router.put("", response_model=SettingsResponse)
def update_settings(body: SettingsUpdateRequest):
    if body.claude_api_key is not None:
        app_settings.claude_api_key = body.claude_api_key
    if body.analysis_score_threshold is not None:
        app_settings.analysis_score_threshold = body.analysis_score_threshold
    return SettingsResponse(
        claude_api_key_set=bool(app_settings.claude_api_key),
        analysis_score_threshold=app_settings.analysis_score_threshold,
        price_cache_ttl_minutes=app_settings.price_cache_ttl_minutes,
    )
