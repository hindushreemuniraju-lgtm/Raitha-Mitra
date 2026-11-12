"""Weather, flood, and classified agricultural risk schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field


class WeatherForecastPoint(BaseModel):
    timestamp: str
    temp_c: float
    humidity_pct: float
    rain_mm: float
    rain_probability_pct: float = 0.0
    wind_kmh: float
    wind_gust_kmh: float = 0.0
    weather_code: int = 0
    condition: str


class DailyForecastPoint(BaseModel):
    date: str
    temp_max_c: float
    temp_min_c: float
    rain_sum_mm: float
    rain_probability_pct: float
    precipitation_hours: float = 0.0
    rain_intensity: str = "dry"  # dry | light | moderate | heavy | very_heavy
    wind_max_kmh: float
    wind_gust_max_kmh: float = 0.0
    weather_code: int = 0
    condition: str


class WeatherWarning(BaseModel):
    severity: str
    title: str
    description: str
    source: str
    issued_at: Optional[str] = None


class FloodAdvisory(BaseModel):
    station: str
    river: str
    level_m: Optional[float] = None
    danger_level_m: Optional[float] = None
    status: str
    source: str
    updated_at: Optional[str] = None


class ClassifiedAlert(BaseModel):
    """Explicitly distinguishes official flood warnings from rainfall warnings and estimated waterlogging."""

    alert_type: str  # official_flood_warning | heavy_rainfall_warning | estimated_waterlogging_risk | general_weather_advisory
    severity: str  # critical | high | medium | low
    title_en: str
    title_kn: str
    message_en: str
    message_kn: str
    source: str
    is_official: bool = False


class WeatherFloodOut(BaseModel):
    location_label: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_source: str = "manual"
    imd_status: str
    imd_source_note: str
    forecast_status: str
    forecast_source: str
    flood_status: str
    flood_source_note: str
    ksndmc_status: str = "not_configured"
    ksndmc_source_note: str = ""
    updated_at: Optional[str] = None
    freshness_label: str
    warnings: List[WeatherWarning]
    forecast: List[WeatherForecastPoint]
    daily_forecast: List[DailyForecastPoint] = Field(default_factory=list)
    flood_advisories: List[FloodAdvisory]
    classified_alerts: List[ClassifiedAlert] = Field(default_factory=list)
