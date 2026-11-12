"""System health and honest integration status endpoints."""

from fastapi import APIRouter

from config import get_settings


router = APIRouter(prefix="/api/v1", tags=["System"])


@router.get("/health")
def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
    }


@router.get("/integrations/status")
def get_integrations_status():
    settings = get_settings()
    return {
        "integrations": settings.integration_statuses(),
    }
