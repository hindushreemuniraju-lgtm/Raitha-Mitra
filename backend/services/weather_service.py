"""Weather & flood orchestration service combining IMD, CWC, KSNDMC, OpenWeather, and Open-Meteo."""

import asyncio
from datetime import datetime, timezone
from typing import List, Optional

from integrations.flood_cwc import CwcFloodAdapter
from integrations.flood_ksndmc import KsndmcFloodAdapter
from integrations.geocoding_nominatim import NominatimGeocodingAdapter
from integrations.weather_imd import ImdWeatherAdapter
from integrations.weather_openmeteo import OpenMeteoAdapter
from integrations.weather_openweather import OpenWeatherAdapter
from models.farmer import Farmer
from schemas.weather import (
    ClassifiedAlert,
    DailyForecastPoint,
    FloodAdvisory,
    WeatherFloodOut,
    WeatherForecastPoint,
    WeatherWarning,
)


def classify_weather_and_flood_risks(
    *,
    location_label: str,
    imd_warnings: List[WeatherWarning],
    flood_advisories: List[FloodAdvisory],
    hourly: List[WeatherForecastPoint],
    daily: List[DailyForecastPoint],
) -> List[ClassifiedAlert]:
    """Strictly separate official flood warnings from heavy rain warnings and estimated waterlogging risk."""
    alerts: List[ClassifiedAlert] = []

    # 1. Official Flood Warning (ONLY from CWC / KSNDMC / IMD official sources — never from rain alone)
    active_official_floods = [
        f
        for f in flood_advisories
        if any(k in (f.status or "").lower() for k in ("warning", "danger", "flood", "release", "alert"))
        or (f.level_m is not None and f.danger_level_m is not None and f.level_m >= f.danger_level_m * 0.95)
    ]
    if active_official_floods:
        stations = ", ".join(f.station for f in active_official_floods[:3])
        alerts.append(
            ClassifiedAlert(
                alert_type="official_flood_warning",
                severity="critical",
                title_en=f"Official Flood / River Level Warning ({stations})",
                title_kn=f"ಅಧಿಕೃತ ಪ್ರವಾಹ / ನದಿ ಮಟ್ಟದ ಎಚ್ಚರಿಕೆ ({stations})",
                message_en=(
                    f"Official flood or reservoir warning reported at {stations}. Move harvested produce and equipment "
                    "to higher ground immediately and follow local district disaster management instructions."
                ),
                message_kn=(
                    f"{stations} ಕೇಂದ್ರದಲ್ಲಿ ಅಧಿಕೃತ ಪ್ರವಾಹ ಅಥವಾ ಜಲಾಶಯ ಎಚ್ಚರಿಕೆ ದಾಖಲಾಗಿದೆ. ಕೊಯ್ಲು ಮಾಡಿದ ಬೆಳೆ ಮತ್ತು "
                    "ಸಲಕರಣೆಗಳನ್ನು ಸುರಕ್ಷಿತ ಎತ್ತರದ ಸ್ಥಳಕ್ಕೆ ಸ್ಥಳಾಂತರಿಸಿ ಮತ್ತು ಜಿಲ್ಲಾಡಳಿತದ ಸೂಚನೆಗಳನ್ನು ಪಾಲಿಸಿ."
                ),
                source=active_official_floods[0].source,
                is_official=True,
            )
        )

    # 2. Official IMD Heavy Rainfall Warnings
    for w in imd_warnings:
        is_heavy = any(k in f"{w.title} {w.description}".lower() for k in ("heavy", "red", "orange", "flood", "thunder"))
        alerts.append(
            ClassifiedAlert(
                alert_type="heavy_rainfall_warning" if is_heavy else "general_weather_advisory",
                severity="high" if w.severity in {"red", "orange", "high"} else "medium",
                title_en=w.title,
                title_kn=f"IMD ಹವಾಮಾನ ಎಚ್ಚರಿಕೆ: {w.title}",
                message_en=w.description,
                message_kn=f"ಭಾರತೀಯ ಹವಾಮಾನ ಇಲಾಖೆ (IMD) ಸೂಚನೆ: {w.description}",
                source=w.source,
                is_official=True,
            )
        )

    # 3. Forecast-derived Rainfall, Thunderstorm, Wind & Estimated Waterlogging Risk
    next_48h = hourly[:48]
    rain_24h_mm = round(sum(p.rain_mm for p in hourly[:24]), 1)
    rain_48h_mm = round(sum(p.rain_mm for p in next_48h), 1)
    max_prob_48h = max((p.rain_probability_pct for p in next_48h), default=0.0)
    max_wind_48h = max((max(p.wind_kmh, p.wind_gust_kmh) for p in next_48h), default=0.0)
    max_temp_48h = max((p.temp_c for p in next_48h), default=25.0)
    min_temp_48h = min((p.temp_c for p in next_48h), default=20.0)
    has_thunderstorm = any(p.weather_code in {95, 96, 99} for p in next_48h)

    tomorrow_rain = daily[1].rain_sum_mm if len(daily) > 1 else rain_24h_mm
    tomorrow_prob = daily[1].rain_probability_pct if len(daily) > 1 else max_prob_48h
    peak_rain_24h = max(rain_24h_mm, daily[0].rain_sum_mm if daily else 0.0, tomorrow_rain)
    peak_prob = max(max_prob_48h, tomorrow_prob)

    if peak_rain_24h >= 35.0:
        alerts.append(
            ClassifiedAlert(
                alert_type="heavy_rainfall_warning",
                severity="high" if peak_rain_24h < 64.5 else "critical",
                title_en=f"Forecasted Heavy Rainfall Alert ({location_label})",
                title_kn=f"ಭಾರೀ ಮಳೆ ಮುನ್ಸೂಚನೆ ಎಚ್ಚರಿಕೆ ({location_label})",
                message_en=(
                    f"Weather forecast indicates heavy rainfall (~{peak_rain_24h:.1f} mm/day, "
                    f"up to {peak_prob:.0f}% probability) in {location_label} within 24-48 hours."
                ),
                message_kn=(
                    f"ಎಚ್ಚರಿಕೆ! ಮುಂದಿನ 24-48 ಗಂಟೆಗಳಲ್ಲಿ {location_label} ಪ್ರದೇಶದಲ್ಲಿ ಸುಮಾರು {peak_rain_24h:.1f} ಮಿ.ಮೀ "
                    f"(ಸಾಧ್ಯತೆ {peak_prob:.0f}%) ಭಾರೀ ಮಳೆಯಾಗುವ ಮುನ್ಸೂಚನೆ ಇದೆ."
                ),
                source="Forecast Model (Non-IMD)",
                is_official=False,
            )
        )
    elif peak_prob >= 60.0 or peak_rain_24h >= 10.0:
        alerts.append(
            ClassifiedAlert(
                alert_type="general_weather_advisory",
                severity="medium",
                title_en=f"Rainfall Forecast Advisory ({location_label})",
                title_kn=f"ಮಳೆ ಮುನ್ಸೂಚನೆ ಸಲಹೆ ({location_label})",
                message_en=(
                    f"Moderate rain expected (~{peak_rain_24h:.1f} mm, {peak_prob:.0f}% probability) over the next 48 hours. "
                    "Plan spraying and fertilizer application during dry hours."
                ),
                message_kn=(
                    f"ಮುಂದಿನ 48 ಗಂಟೆಗಳಲ್ಲಿ {location_label} ಭಾಗದಲ್ಲಿ ಸಾಧಾರಣ ಮಳೆ ({peak_rain_24h:.1f} ಮಿ.ಮೀ, {peak_prob:.0f}% ಸಾಧ್ಯತೆ) ನಿರೀಕ್ಷಿತವಾಗಿದೆ. "
                    "ಸಿಂಪಡಣೆ ಮತ್ತು ಗೊಬ್ಬರ ಹಾಕುವ ಕೆಲಸವನ್ನು ಒಣ ಸಮಯದಲ್ಲಿ ಯೋಜಿಸಿ."
                ),
                source="Forecast Model (Non-IMD)",
                is_official=False,
            )
        )

    # Estimated Waterlogging Risk (explicitly NOT an active flood warning!)
    if rain_48h_mm >= 45.0 or peak_rain_24h >= 35.0:
        alerts.append(
            ClassifiedAlert(
                alert_type="estimated_waterlogging_risk",
                severity="high",
                title_en="Estimated Field Waterlogging Risk (Forecast-Based)",
                title_kn="ಅಂದಾಜು ಹೊಲದ ನೀರು ನಿಲ್ಲುವ ಅಪಾಯ (ಮುನ್ಸೂಚನೆ ಆಧಾರಿತ)",
                message_en=(
                    f"Forecasted {rain_48h_mm:.1f} mm 48h rainfall may cause localized waterlogging in low-lying or poorly drained fields. "
                    "This is an estimated drainage advisory—not an official river flood warning. Clear bund outlets and protect stored inputs."
                ),
                message_kn=(
                    f"ಮುಂದಿನ 48 ಗಂಟೆಗಳಲ್ಲಿ {rain_48h_mm:.1f} ಮಿ.ಮೀ ಮಳೆಯಿಂದ ತಗ್ಗು ಹೊಲಗಳಲ್ಲಿ ನೀರು ನಿಲ್ಲುವ ಅಂದಾಜು ಅಪಾಯವಿದೆ. "
                    "ಇದು ಅಧಿಕೃತ ನದಿ ಪ್ರವಾಹ ಎಚ್ಚರಿಕೆಯಲ್ಲ; ಹೊಲದ ಕಾಲುವೆಗಳನ್ನು ಸ್ವಚ್ಛಗೊಳಿಸಿ ಮತ್ತು ಗೊಬ್ಬರ/ಬೆಳೆಯನ್ನು ಸುರಕ್ಷಿತವಾಗಿಡಿ."
                ),
                source="Waterlogging Risk Estimator",
                is_official=False,
            )
        )

    if has_thunderstorm or max_wind_48h >= 40.0:
        alerts.append(
            ClassifiedAlert(
                alert_type="general_weather_advisory",
                severity="high" if has_thunderstorm else "medium",
                title_en="Thunderstorm / Strong Wind Gust Advisory",
                title_kn="ಗುಡುಗು ಸಹಿತ ಮಳೆ / ಬಲವಾದ ಗಾಳಿ ಸಲಹೆ",
                message_en=(
                    f"Gusts up to {max_wind_48h:.0f} km/h{' and thunderstorm activity' if has_thunderstorm else ''} forecast in the next 48 hours. "
                    "Check banana/tomato staking and avoid open-field work during lightning."
                ),
                message_kn=(
                    f"ಮುಂದಿನ 48 ಗಂಟೆಗಳಲ್ಲಿ ಗಂಟೆಗೆ {max_wind_48h:.0f} ಕಿ.ಮೀ ವೇಗದ ಗಾಳಿ{' ಹಾಗೂ ಗುಡುಗು ಮಿಂಚು' if has_thunderstorm else ''} ಸಾಧ್ಯತೆಯಿದೆ. "
                    "ಬಾಳೆ/ಟೊಮೇಟೊ ಆಧಾರ ಕಂಬಗಳನ್ನು ಭದ್ರಪಡಿಸಿ."
                ),
                source="Forecast Model",
                is_official=False,
            )
        )

    if max_temp_48h >= 39.0 or min_temp_48h <= 10.0:
        is_hot = max_temp_48h >= 39.0
        alerts.append(
            ClassifiedAlert(
                alert_type="general_weather_advisory",
                severity="medium",
                title_en=f"Extreme {'Heat' if is_hot else 'Cold'} Advisory",
                title_kn=f"{'ಅತಿಯಾದ ಬಿಸಿಲು' if is_hot else 'ತೀವ್ರ ಚಳಿ'} ಹವಾಮಾನ ಸಲಹೆ",
                message_en=(
                    f"Forecast temperatures reach {max_temp_48h:.1f}°C (min {min_temp_48h:.1f}°C). "
                    + ("Schedule irrigation in early morning/evening to minimize flower drop." if is_hot else "Protect tender seedlings with light evening irrigation or mulching.")
                ),
                message_kn=(
                    f"ತಾಪಮಾನ ಗರಿಷ್ಠ {max_temp_48h:.1f}°C (ಕನಿಷ್ಠ {min_temp_48h:.1f}°C) ತಲುಪುವ ಸಾಧ್ಯತೆ ಇದೆ. "
                    + ("ಹೂವು ಉದುರುವುದನ್ನು ತಡೆಯಲು ಬೆಳಿಗ್ಗೆ ಅಥವಾ ಸಂಜೆ ನೀರಾವರಿ ನೀಡಿ." if is_hot else "ಸಸಿಗಳನ್ನು ರಕ್ಷಿಸಲು ಮಲ್ಚಿಂಗ್ ಅಥವಾ ಸಂಜೆ ಲಘು ನೀರಾವರಿ ಮಾಡಿ.")
                ),
                source="Forecast Model",
                is_official=False,
            )
        )

    return alerts


async def get_weather_and_flood_summary(
    farmer: Farmer,
    *,
    state_override: Optional[str] = None,
    district_override: Optional[str] = None,
    lat_override: Optional[float] = None,
    lon_override: Optional[float] = None,
) -> WeatherFloodOut:
    state = (state_override or farmer.state or "").strip()
    district = (district_override or farmer.district or "").strip()
    village = (farmer.village or "").strip()
    taluk = (getattr(farmer, "taluk", "") or "").strip()

    lat = lat_override if lat_override is not None else (farmer.latitude if farmer.gps_consent else None)
    lon = lon_override if lon_override is not None else (farmer.longitude if farmer.gps_consent else None)
    loc_source = "gps" if (lat is not None and lon is not None) else "manual"

    # Never substitute a hardcoded Bengaluru fallback. Forward-geocode explicit manual location only if provided.
    if (lat is None or lon is None) and any([village, taluk, district, state]):
        query_parts = [p for p in [village, taluk, district, state, "India"] if p]
        geo = NominatimGeocodingAdapter()
        coords = await geo.forward_geocode(", ".join(query_parts))
        if coords:
            lat = coords["lat"]
            lon = coords["lon"]
            loc_source = "geocoded_manual"

    imd = ImdWeatherAdapter()
    owm = OpenWeatherAdapter()
    om = OpenMeteoAdapter()
    cwc = CwcFloodAdapter()
    ksndmc = KsndmcFloodAdapter()

    district_query = district or village or taluk or state or "Unknown"

    tasks = [
        imd.fetch_district_warnings(state or "Karnataka", district_query),
        cwc.fetch_flood_advisories(state or "Karnataka", district_query),
        ksndmc.fetch_karnataka_alerts(state or "Karnataka", district_query),
    ]
    if lat is not None and lon is not None:
        tasks.append(om.fetch_forecast(lat, lon))
    if owm.is_configured:
        tasks.append(owm.fetch_forecast(city_query=district_query, lat=lat, lon=lon))

    results = await asyncio.gather(*tasks)
    imd_res, cwc_res, ksndmc_res = results[0], results[1], results[2]
    idx = 3
    om_res = results[idx] if (lat is not None and lon is not None) else None
    if om_res is not None:
        idx += 1
    owm_res = results[idx] if owm.is_configured else None

    hourly_points: List[WeatherForecastPoint] = []
    daily_points: List[DailyForecastPoint] = []
    forecast_status = "not_configured"
    forecast_source = "No location coordinates available"
    forecast_updated = None

    if om_res and om_res.get("status") == "configured":
        hourly_points = [WeatherForecastPoint(**p) for p in om_res.get("hourly", [])]
        daily_points = [DailyForecastPoint(**d) for d in om_res.get("daily", [])]
        forecast_status = "configured"
        forecast_source = om_res.get("source", "Open-Meteo Live Forecast")
        forecast_updated = om_res.get("updated_at")
    elif owm_res and owm_res.get("status") == "configured":
        hourly_points = [WeatherForecastPoint(**p) for p in owm_res.get("forecast", [])]
        forecast_status = "configured"
        forecast_source = owm_res.get("source", "OpenWeatherMap")
        forecast_updated = owm_res.get("updated_at")
    elif om_res and om_res.get("status") == "error":
        forecast_status = "error"
        forecast_source = om_res.get("note", "Open-Meteo unavailable")

    imd_warnings = [WeatherWarning(**w) for w in imd_res.get("warnings", [])]
    combined_flood_raw = list(cwc_res.get("advisories", [])) + list(ksndmc_res.get("advisories", []))
    flood_advisories = [FloodAdvisory(**a) for a in combined_flood_raw]

    label_parts = [p for p in [village, taluk, district, state] if p]
    location_label = ", ".join(dict.fromkeys(label_parts)) or (f"{lat:.4f}, {lon:.4f}" if lat is not None else "Location not set")

    classified = classify_weather_and_flood_risks(
        location_label=location_label,
        imd_warnings=imd_warnings,
        flood_advisories=flood_advisories,
        hourly=hourly_points,
        daily=daily_points,
    )

    updated_at = (
        imd_res.get("updated_at")
        or forecast_updated
        or cwc_res.get("updated_at")
        or ksndmc_res.get("updated_at")
    )
    freshness = (
        f"Updated at {datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}"
        if updated_at
        else "Live external weather feeds unavailable"
    )

    return WeatherFloodOut(
        location_label=location_label,
        latitude=lat,
        longitude=lon,
        location_source=loc_source,
        imd_status=imd_res["status"],
        imd_source_note=imd_res["note"],
        forecast_status=forecast_status,
        forecast_source=forecast_source,
        flood_status=cwc_res["status"],
        flood_source_note=cwc_res["note"],
        ksndmc_status=ksndmc_res["status"],
        ksndmc_source_note=ksndmc_res["note"],
        updated_at=updated_at,
        freshness_label=freshness,
        warnings=imd_warnings,
        forecast=hourly_points,
        daily_forecast=daily_points,
        flood_advisories=flood_advisories,
        classified_alerts=classified,
    )
