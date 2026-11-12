"""Weather and flood router."""

from typing import Optional

from fastapi import APIRouter, Depends

from models.farmer import Farmer
from schemas.weather import WeatherFloodOut
from services.weather_service import get_weather_and_flood_summary
from utils.security import get_current_farmer


router = APIRouter(prefix="/api/v1/weather", tags=["Weather & Flood"])


@router.get("", response_model=WeatherFloodOut)
async def get_weather(
    state: Optional[str] = None,
    district: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    current_farmer: Farmer = Depends(get_current_farmer),
):
    return await get_weather_and_flood_summary(
        current_farmer,
        state_override=state,
        district_override=district,
        lat_override=lat,
        lon_override=lon,
    )
