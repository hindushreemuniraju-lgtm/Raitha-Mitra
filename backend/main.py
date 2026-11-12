"""FastAPI application entry point for Raitha Mitra."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import Base, SessionLocal, engine
import models  # noqa: F401
from routers import (
    auth,
    crops,
    dashboard,
    farmers,
    fertilizer,
    files,
    harvest,
    location,
    mandi,
    notifications,
    nutrition,
    pests,
    profit,
    schemes,
    soil,
    system,
    voice,
    weather,
    yield_prediction,
)
from services.monitoring_service import run_monitoring_all_farmers
from utils.logging_utils import configure_logging


settings = get_settings()

configure_logging(
    secrets_to_mask=[
        settings.SECRET_KEY,
        settings.SARVAM_API_KEY,
        settings.LIVEKIT_API_SECRET,
        settings.IMD_API_KEY,
        settings.IMD_PASSWORD,
        settings.OPENWEATHER_API_KEY,
        settings.CWC_API_KEY,
        settings.PLANTIX_API_KEY,
        settings.VISION_MODEL_API_KEY,
        settings.GOOGLE_AGRI_API_KEY,
        settings.USDA_FDC_API_KEY,
        settings.NCBI_API_KEY,
        settings.DATA_GOV_IN_API_KEY,
        settings.CEDA_API_KEY,
        settings.APISETU_API_KEY,
        settings.FERTILIZER_PRICE_API_KEY,
    ]
)


async def _monitoring_worker() -> None:
    while True:
        await asyncio.sleep(max(300, settings.MONITORING_INTERVAL_SECONDS))
        db = SessionLocal()
        try:
            await run_monitoring_all_farmers(db, trigger="scheduler")
        except Exception:
            pass
        finally:
            db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.APP_ENV == "development" or settings.DATABASE_URL.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
    task = None
    if settings.MONITORING_SCHEDULER_ENABLED:
        task = asyncio.create_task(_monitoring_worker())
    try:
        yield
    finally:
        if task:
            task.cancel()


app = FastAPI(
    title="Raitha Mitra API",
    description="AI-powered smart farming companion API for Indian farmers.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(system.router)
app.include_router(auth.router)
app.include_router(farmers.router)
app.include_router(files.router)
app.include_router(location.router)
app.include_router(dashboard.router)
app.include_router(weather.router)
app.include_router(harvest.router)
app.include_router(notifications.router)
app.include_router(soil.router)
app.include_router(crops.router)
app.include_router(pests.router)
app.include_router(fertilizer.router)
app.include_router(yield_prediction.router)
app.include_router(nutrition.router)
app.include_router(mandi.router)
app.include_router(profit.router)
app.include_router(schemes.router)
app.include_router(voice.router)
