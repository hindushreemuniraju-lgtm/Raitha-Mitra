"""Application settings and integration configuration status helpers."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent
_IS_VERCEL = bool(os.environ.get("VERCEL"))
_DEFAULT_DB_URL = (
    "sqlite:////tmp/raithamitra.db"
    if _IS_VERCEL
    else f"sqlite:///{(BACKEND_DIR / 'raithamitra.db').as_posix()}"
)
_DEFAULT_UPLOAD_DIR = "/tmp/uploads" if _IS_VERCEL else str(BACKEND_DIR / "uploads")


class Settings(BaseSettings):
    """Typed runtime configuration loaded from backend/.env and environment."""

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    APP_NAME: str = "Raitha Mitra"
    SECRET_KEY: str = "dev-only-insecure-secret-change-me-32bytes"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = _DEFAULT_DB_URL
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    MAX_UPLOAD_MB: int = 10
    UPLOAD_DIR: str = _DEFAULT_UPLOAD_DIR
    SOIL_DATASET_PATH: str = str(BACKEND_DIR / "data" / "soil_datasets")

    # Voice (LiveKit + Sarvam AI)
    LIVEKIT_URL: str = ""
    LIVEKIT_API_KEY: str = ""
    LIVEKIT_API_SECRET: str = ""
    SARVAM_API_KEY: str = ""
    SARVAM_STT_MODEL: str = "saaras:v4"
    SARVAM_TTS_MODEL: str = "bulbul:v4-flash"
    SARVAM_LLM_MODEL: str = "sarvam-105b"

    # Weather & Flood
    IMD_API_BASE_URL: str = "https://api.imd.gov.in"
    IMD_API_KEY: str = ""
    IMD_USERNAME: str = ""
    IMD_PASSWORD: str = ""
    IMD_WARNINGS_PATH: str = "/api/v1/district_warning"
    IMD_FORECAST_PATH: str = "/api/v1/cityforecast"

    OPENWEATHER_API_KEY: str = ""
    OPENWEATHER_MODE: str = Field(default="2.5")

    CWC_API_URL: str = ""
    CWC_API_KEY: str = ""

    # Pest & Disease Detection
    PLANTIX_BASE_URL: str = ""
    PLANTIX_API_KEY: str = ""
    VISION_MODEL_BASE_URL: str = ""
    VISION_MODEL_API_KEY: str = ""
    VISION_MODEL_NAME: str = ""

    # Yield & Landscape Metadata
    GOOGLE_AGRI_API_KEY: str = ""

    # Nutrition
    USDA_FDC_API_KEY: str = ""
    NCBI_API_KEY: str = ""
    NCBI_TOOL_NAME: str = "RaithaMitra"
    NCBI_CONTACT_EMAIL: str = "support@raithamitra.local"

    # Mandi Prices
    DATA_GOV_IN_API_KEY: str = ""
    CEDA_API_KEY: str = ""
    CEDA_AUTH_HEADER: str = "x-api-key"
    ENAM_API_URL: str = ""

    # Government Schemes
    APISETU_API_KEY: str = ""
    APISETU_CLIENT_ID: str = ""

    # Fertilizer MRP Feed
    FERTILIZER_PRICE_API_URL: str = ""
    FERTILIZER_PRICE_API_KEY: str = ""

    # Live Geocoding, Karnataka Disaster Management & Scheduled Monitoring
    NOMINATIM_USER_AGENT: str = "RaithaMitra/1.0 (contact@raithamitra.app)"
    KSNDMC_FLOOD_API_URL: str = ""
    KSNDMC_API_KEY: str = ""
    MONITORING_SCHEDULER_ENABLED: bool = not _IS_VERCEL
    MONITORING_INTERVAL_SECONDS: int = 1800
    CRON_SECRET: str = ""

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    def integration_statuses(self) -> Dict[str, dict]:
        """Return honest configuration status for every external service (never leaks secrets)."""
        return {
            "livekit": {
                "name": "LiveKit Real-Time Voice",
                "configured": bool(self.LIVEKIT_URL and self.LIVEKIT_API_KEY and self.LIVEKIT_API_SECRET),
                "status": "configured"
                if (self.LIVEKIT_URL and self.LIVEKIT_API_KEY and self.LIVEKIT_API_SECRET)
                else "not_configured",
                "note": "Requires LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET.",
            },
            "sarvam_ai": {
                "name": "Sarvam AI (Saaras STT, Bulbul TTS, Sarvam LLM)",
                "configured": bool(self.SARVAM_API_KEY),
                "status": "configured" if self.SARVAM_API_KEY else "not_configured",
                "note": "Requires SARVAM_API_KEY subscription credentials.",
            },
            "imd_weather": {
                "name": "India Meteorological Department (IMD)",
                "configured": bool(self.IMD_API_KEY or (self.IMD_USERNAME and self.IMD_PASSWORD)),
                "status": "configured"
                if (self.IMD_API_KEY or (self.IMD_USERNAME and self.IMD_PASSWORD))
                else "not_configured",
                "note": "Primary source for Indian weather warnings; requires IMD portal registration & IP whitelisting.",
            },
            "openweather": {
                "name": "OpenWeatherMap (Forecast Fallback Only)",
                "configured": bool(self.OPENWEATHER_API_KEY),
                "status": "configured" if self.OPENWEATHER_API_KEY else "not_configured",
                "note": f"Fallback for forecasts only (mode {self.OPENWEATHER_MODE}); never generates IMD warnings.",
            },
            "cwc_flood": {
                "name": "Central Water Commission (CWC Flood Portal)",
                "configured": bool(self.CWC_API_URL),
                "status": "configured" if self.CWC_API_URL else "not_configured",
                "note": "CWC ffs.india-water.gov.in has no public self-service REST API; requires institutional feed URL.",
            },
            "soil_datasets": {
                "name": "SoilGrids / Bhuvan Downloadable Datasets",
                "configured": Path(self.SOIL_DATASET_PATH).exists(),
                "status": "configured" if Path(self.SOIL_DATASET_PATH).exists() else "not_configured",
                "note": "Uses local downloaded SoilGrids GeoTIFF/CSV or Bhuvan extracts (never paused REST API).",
            },
            "plantix": {
                "name": "Plantix Intelligence B2B API",
                "configured": bool(self.PLANTIX_API_KEY and self.PLANTIX_BASE_URL),
                "status": "configured" if (self.PLANTIX_API_KEY and self.PLANTIX_BASE_URL) else "not_configured",
                "note": "Requires Plantix B2B partner approval & endpoint host.",
            },
            "vision_fallback": {
                "name": "Pluggable Disease Vision Model",
                "configured": bool(self.VISION_MODEL_API_KEY and self.VISION_MODEL_BASE_URL and self.VISION_MODEL_NAME),
                "status": "configured"
                if (self.VISION_MODEL_API_KEY and self.VISION_MODEL_BASE_URL and self.VISION_MODEL_NAME)
                else "not_configured",
                "note": "Optional multimodal vision fallback when Plantix is unavailable.",
            },
            "google_agri": {
                "name": "Google Agricultural Understanding (ALU/AMED)",
                "configured": bool(self.GOOGLE_AGRI_API_KEY),
                "status": "configured" if self.GOOGLE_AGRI_API_KEY else "not_configured",
                "note": "Provides landscape boundaries & sowing/harvest metadata only (no yield endpoint).",
            },
            "usda_fdc": {
                "name": "USDA FoodData Central",
                "configured": bool(self.USDA_FDC_API_KEY),
                "status": "configured" if self.USDA_FDC_API_KEY else "not_configured",
                "note": "Requires free fdc.nal.usda.gov / api.data.gov key.",
            },
            "pubmed": {
                "name": "NCBI PubMed E-utilities",
                "configured": True,
                "status": "configured",
                "note": "Public E-utilities access enabled (3 req/s without key, 10 req/s with NCBI_API_KEY).",
            },
            "data_gov_in": {
                "name": "data.gov.in AGMARKNET & Schemes",
                "configured": bool(self.DATA_GOV_IN_API_KEY),
                "status": "configured" if self.DATA_GOV_IN_API_KEY else "not_configured",
                "note": "Requires free data.gov.in API key.",
            },
            "ceda_agmarknet": {
                "name": "CEDA Ashoka Agmarknet API",
                "configured": bool(self.CEDA_API_KEY),
                "status": "configured" if self.CEDA_API_KEY else "not_configured",
                "note": "Requires free CEDA Data Portal API registration.",
            },
            "enam": {
                "name": "e-NAM Portal Feed",
                "configured": bool(self.ENAM_API_URL),
                "status": "configured" if self.ENAM_API_URL else "not_configured",
                "note": "No public self-service REST API documented on enam.gov.in.",
            },
            "apisetu_myscheme": {
                "name": "API Setu myScheme",
                "configured": bool(self.APISETU_API_KEY and self.APISETU_CLIENT_ID),
                "status": "configured" if (self.APISETU_API_KEY and self.APISETU_CLIENT_ID) else "not_configured",
                "note": "Requires API Setu registration; official verified .gov.in scheme catalog also available.",
            },
            "fertilizer_prices": {
                "name": "Verified Fertilizer MRP Feed",
                "configured": bool(self.FERTILIZER_PRICE_API_URL),
                "status": "configured" if self.FERTILIZER_PRICE_API_URL else "not_configured",
                "note": "Prices shown only when verified source and date are available.",
            },
            "openmeteo": {
                "name": "Open-Meteo Weather Forecast",
                "configured": True,
                "status": "configured",
                "note": "Real-time hourly/daily rainfall, intensity, wind, and temperature forecasts by farm GPS coordinates.",
            },
            "nominatim_geocoding": {
                "name": "OpenStreetMap Nominatim Geocoding",
                "configured": True,
                "status": "configured",
                "note": "Reverse-geocodes device GPS coordinates into village, taluk, district, and state.",
            },
            "ksndmc_flood": {
                "name": "Karnataka KSNDMC Disaster Feed",
                "configured": bool(self.KSNDMC_FLOOD_API_URL),
                "status": "configured" if self.KSNDMC_FLOOD_API_URL else "not_configured",
                "note": "Official ksndmc.karnataka.gov.in feed URL optional; without institutional feed, estimated waterlogging risks are labelled clearly.",
            },
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
