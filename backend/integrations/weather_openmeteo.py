"""Open-Meteo weather forecast adapter (hourly & daily rainfall, probability, wind, thunderstorm WMO codes)."""

from datetime import datetime, timezone
from typing import Any, Dict, List

from integrations.base import BaseIntegrationClient, IntegrationError


_WMO_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _describe_wmo(code: Any) -> str:
    try:
        return _WMO_DESCRIPTIONS.get(int(code), f"Weather code {code}")
    except (TypeError, ValueError):
        return "Forecast available"


class OpenMeteoAdapter(BaseIntegrationClient):
    """Real-time open-access forecast adapter using Open-Meteo /v1/forecast."""

    service_name = "openmeteo"

    def __init__(self):
        super().__init__(
            base_url="https://api.open-meteo.com",
            timeout_seconds=10.0,
            max_retries=2,
            cache_ttl_seconds=900,
        )

    @property
    def is_configured(self) -> bool:
        return True

    async def fetch_forecast(self, lat: float, lon: float) -> Dict[str, Any]:
        try:
            data = await self.request_json(
                "GET",
                "/v1/forecast",
                params={
                    "latitude": round(lat, 5),
                    "longitude": round(lon, 5),
                    "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m,wind_gusts_10m",
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,precipitation_hours,wind_speed_10m_max,wind_gusts_10m_max",
                    "forecast_days": 7,
                    "timezone": "auto",
                },
                cache_key=f"openmeteo:{lat:.3f}:{lon:.3f}",
                cache_ttl=900,
            )

            hourly_raw = data.get("hourly") or {}
            h_times = hourly_raw.get("time") or []
            h_temps = hourly_raw.get("temperature_2m") or []
            h_hums = hourly_raw.get("relative_humidity_2m") or []
            h_probs = hourly_raw.get("precipitation_probability") or []
            h_prec = hourly_raw.get("precipitation") or []
            h_codes = hourly_raw.get("weather_code") or []
            h_winds = hourly_raw.get("wind_speed_10m") or []
            h_gusts = hourly_raw.get("wind_gusts_10m") or []

            hourly_points: List[Dict[str, Any]] = []
            for idx, ts in enumerate(h_times[:48]):
                code = h_codes[idx] if idx < len(h_codes) else 0
                hourly_points.append(
                    {
                        "timestamp": str(ts),
                        "temp_c": float(h_temps[idx]) if idx < len(h_temps) and h_temps[idx] is not None else 0.0,
                        "humidity_pct": float(h_hums[idx]) if idx < len(h_hums) and h_hums[idx] is not None else 0.0,
                        "rain_mm": float(h_prec[idx]) if idx < len(h_prec) and h_prec[idx] is not None else 0.0,
                        "rain_probability_pct": float(h_probs[idx]) if idx < len(h_probs) and h_probs[idx] is not None else 0.0,
                        "wind_kmh": float(h_winds[idx]) if idx < len(h_winds) and h_winds[idx] is not None else 0.0,
                        "wind_gust_kmh": float(h_gusts[idx]) if idx < len(h_gusts) and h_gusts[idx] is not None else 0.0,
                        "weather_code": int(code) if code is not None else 0,
                        "condition": _describe_wmo(code),
                    }
                )

            daily_raw = data.get("daily") or {}
            d_times = daily_raw.get("time") or []
            d_codes = daily_raw.get("weather_code") or []
            d_tmax = daily_raw.get("temperature_2m_max") or []
            d_tmin = daily_raw.get("temperature_2m_min") or []
            d_psum = daily_raw.get("precipitation_sum") or []
            d_pprob = daily_raw.get("precipitation_probability_max") or []
            d_phours = daily_raw.get("precipitation_hours") or []
            d_wmax = daily_raw.get("wind_speed_10m_max") or []
            d_gmax = daily_raw.get("wind_gusts_10m_max") or []

            daily_points: List[Dict[str, Any]] = []
            for idx, day in enumerate(d_times[:7]):
                code = d_codes[idx] if idx < len(d_codes) else 0
                rain_sum = float(d_psum[idx]) if idx < len(d_psum) and d_psum[idx] is not None else 0.0
                rain_prob = float(d_pprob[idx]) if idx < len(d_pprob) and d_pprob[idx] is not None else 0.0
                tmax = float(d_tmax[idx]) if idx < len(d_tmax) and d_tmax[idx] is not None else 0.0
                tmin = float(d_tmin[idx]) if idx < len(d_tmin) and d_tmin[idx] is not None else 0.0
                wmax = float(d_wmax[idx]) if idx < len(d_wmax) and d_wmax[idx] is not None else 0.0
                gmax = float(d_gmax[idx]) if idx < len(d_gmax) and d_gmax[idx] is not None else 0.0
                phours = float(d_phours[idx]) if idx < len(d_phours) and d_phours[idx] is not None else 0.0
                intensity = (
                    "very_heavy"
                    if rain_sum >= 64.5
                    else "heavy"
                    if rain_sum >= 35.0
                    else "moderate"
                    if rain_sum >= 10.0
                    else "light"
                    if rain_sum > 0.5
                    else "dry"
                )
                daily_points.append(
                    {
                        "date": str(day),
                        "temp_max_c": tmax,
                        "temp_min_c": tmin,
                        "rain_sum_mm": round(rain_sum, 1),
                        "rain_probability_pct": round(rain_prob, 0),
                        "precipitation_hours": phours,
                        "rain_intensity": intensity,
                        "wind_max_kmh": round(wmax, 1),
                        "wind_gust_max_kmh": round(gmax, 1),
                        "weather_code": int(code) if code is not None else 0,
                        "condition": _describe_wmo(code),
                    }
                )

            return {
                "status": "configured",
                "source": "Open-Meteo Live Forecast",
                "hourly": hourly_points,
                "daily": daily_points,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        except IntegrationError as exc:
            return {
                "status": "error",
                "source": "Open-Meteo Live Forecast",
                "note": exc.message,
                "hourly": [],
                "daily": [],
                "updated_at": None,
            }
