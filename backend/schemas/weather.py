"""Weather and flood schemas."""

from typing import List, Optional

from pydantic import BaseModel


class WeatherForecastPoint(BaseModel):
    timestamp: str
    temp_c: float
    humidity_pct: float
    rain_mm: float
    wind_kmh: float
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


class WeatherFloodOut(BaseModel):
    location_label: str
    imd_status: str
    imd_source_note: str
    forecast_status: str
    forecast_source: str
    flood_status: str
    flood_source_note: str
    updated_at: Optional[str] = None
    freshness_label: str
    warnings: List[WeatherWarning]
    forecast: List[WeatherForecastPoint]
    flood_advisories: List[FloodAdvisory]
