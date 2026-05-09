from pathlib import Path

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.scan import VersionResponse


router = APIRouter(prefix="/api", tags=["version"])


@router.get("/version", response_model=VersionResponse)
def version() -> VersionResponse:
    checkpoint_configured = bool(settings.MODEL_CHECKPOINT_PATH and Path(settings.MODEL_CHECKPOINT_PATH).exists())
    return VersionResponse(
        app_name=settings.PROJECT_NAME,
        api_version=settings.API_VERSION,
        model_name=settings.MODEL_NAME,
        model_version=settings.MODEL_VERSION,
        model_hash=settings.MODEL_HASH,
        checkpoint_configured=checkpoint_configured,
        clinical_use="not_validated_for_clinical_use",
    )

