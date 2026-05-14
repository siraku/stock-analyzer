from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings as app_settings

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    openrouter_api_key_set: bool
    openrouter_model: str
    analysis_score_threshold: int
    price_cache_ttl_minutes: int


class SettingsUpdateRequest(BaseModel):
    openrouter_api_key: str | None = None
    openrouter_model: str | None = None
    analysis_score_threshold: int | None = None


@router.get("", response_model=SettingsResponse)
def get_settings():
    return SettingsResponse(
        openrouter_api_key_set=bool(app_settings.openrouter_api_key),
        openrouter_model=app_settings.openrouter_model,
        analysis_score_threshold=app_settings.analysis_score_threshold,
        price_cache_ttl_minutes=app_settings.price_cache_ttl_minutes,
    )


@router.put("", response_model=SettingsResponse)
def update_settings(body: SettingsUpdateRequest):
    if body.openrouter_api_key is not None:
        app_settings.openrouter_api_key = body.openrouter_api_key
    if body.openrouter_model is not None:
        app_settings.openrouter_model = body.openrouter_model
    if body.analysis_score_threshold is not None:
        app_settings.analysis_score_threshold = body.analysis_score_threshold
    return SettingsResponse(
        openrouter_api_key_set=bool(app_settings.openrouter_api_key),
        openrouter_model=app_settings.openrouter_model,
        analysis_score_threshold=app_settings.analysis_score_threshold,
        price_cache_ttl_minutes=app_settings.price_cache_ttl_minutes,
    )
