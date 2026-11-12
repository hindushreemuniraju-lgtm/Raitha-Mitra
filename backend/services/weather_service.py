"""Weather and flood orchestration service (IMD primary warnings, OpenWeather fallback forecast, CWC flood)."""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from integrations.flood_cwc import CwcFloodAdapter
from integrations.weather_imd import ImdWeatherAdapter
from integrations.weather_openweather import OpenWeatherAdapter
from models.farmer import Farmer
from schemas.weather import WeatherFloodOut


async def get_weather_and_flood_summary(
    farmer: Farmer,
    *,
    state_override: Optional[str] = None,
    district_override: Optional[str] = None,
    lat_override: Optional[float] = None,
    lon_override: Optional[float] = None,
) -> WeatherFloodOut:
    state = (state_override or farmer.state or "Karnataka").strip()
    district = (district_override or farmer.district or farmer.village or state).strip()
    lat = lat_override if lat_override is not None else (farmer.latitude if farmer.gps_consent else None)
    lon = lon_override if lon_override is not None else (farmer.longitude if farmer.gps_consent else None)

    imd = ImdWeatherAdapter()
    owm = OpenWeatherAdapter()
    cwc = CwcFloodAdapter()

    imd_res, owm_res, cwc_res = await asyncio.gather(
        imd.fetch_district_warnings(state, district),
        owm.fetch_forecast(city_query=district, lat=lat, lon=lon),
        cwc.fetch_flood_advisories(state, district),
    )

    updated_at = imd_res.get("updated_at") or owm_res.get("updated_at") or cwc_res.get("updated_at")
    freshness = (
        f"Updated at {datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}"
        if updated_at
        else "Live external feeds not configured"
    )

    return WeatherFloodOut(
        location_label=f"{district}, {state}",
        imd_status=imd_res["status"],
        imd_source_note=imd_res["note"],
        forecast_status=owm_res["status"],
        forecast_source=owm_res["source"],
        flood_status=cwc_res["status"],
        flood_source_note=cwc_res["note"],
        updated_at=updated_at,
        freshness_label=freshness,
        warnings=imd_res["warnings"],
        forecast=owm_res["forecast"],
        flood_advisories=cwc_res["advisories"],
    )
