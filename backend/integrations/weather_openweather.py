"""OpenWeatherMap adapter strictly for forecast fallback (never warnings)."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config import get_settings
from integrations.base import BaseIntegrationClient, IntegrationError


class OpenWeatherAdapter(BaseIntegrationClient):
    """Fallback weather forecast adapter using OpenWeather 2.5 free tier or 3.0 One Call."""

    service_name = "openweather"

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url="https://api.openweathermap.org",
            timeout_seconds=10.0,
            max_retries=2,
            cache_ttl_seconds=900,
        )
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.OPENWEATHER_API_KEY)

    async def fetch_forecast(
        self,
        *,
        city_query: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
    ) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "status": "not_configured",
                "source": "OpenWeatherMap",
                "note": "OPENWEATHER_API_KEY not configured.",
                "forecast": [],
                "updated_at": None,
            }

        params: Dict[str, Any] = {
            "appid": self.settings.OPENWEATHER_API_KEY,
            "units": "metric",
        }
        if lat is not None and lon is not None:
            params["lat"] = lat
            params["lon"] = lon
        elif city_query:
            params["q"] = f"{city_query},IN"
        else:
            return {
                "status": "error",
                "source": "OpenWeatherMap",
                "note": "Location (city/district or GPS coordinates) required for OpenWeather forecast.",
                "forecast": [],
                "updated_at": None,
            }

        try:
            if self.settings.OPENWEATHER_MODE == "3.0" and lat is not None and lon is not None:
                data = await self.request_json(
                    "GET",
                    "/data/3.0/onecall",
                    params={**params, "exclude": "minutely,alerts"},
                    cache_key=f"owm3:{lat}:{lon}",
                )
                points: List[Dict[str, Any]] = []
                for item in (data.get("daily") or [])[:7]:
                    dt_iso = datetime.fromtimestamp(item["dt"], tz=timezone.utc).isoformat()
                    points.append(
                        {
                            "timestamp": dt_iso,
                            "temp_c": float(item.get("temp", {}).get("day", 0.0)),
                            "humidity_pct": float(item.get("humidity", 0.0)),
                            "rain_mm": float(item.get("rain", 0.0)),
                            "wind_kmh": round(float(item.get("wind_speed", 0.0)) * 3.6, 1),
                            "condition": (item.get("weather") or [{}])[0].get("description", "Forecast"),
                        }
                    )
                source_label = "OpenWeatherMap One Call 3.0 (Forecast Fallback)"
            else:
                data = await self.request_json(
                    "GET",
                    "/data/2.5/forecast",
                    params=params,
                    cache_key=f"owm25:{city_query or ''}:{lat}:{lon}",
                )
                points = []
                for item in (data.get("list") or [])[:12]:
                    points.append(
                        {
                            "timestamp": item.get("dt_txt", ""),
                            "temp_c": float(item.get("main", {}).get("temp", 0.0)),
                            "humidity_pct": float(item.get("main", {}).get("humidity", 0.0)),
                            "rain_mm": float((item.get("rain") or {}).get("3h", 0.0)),
                            "wind_kmh": round(float((item.get("wind") or {}).get("speed", 0.0)) * 3.6, 1),
                            "condition": (item.get("weather") or [{}])[0].get("description", "Forecast"),
                        }
                    )
                source_label = "OpenWeatherMap 2.5 Forecast (Fallback Only)"

            return {
                "status": "configured",
                "source": source_label,
                "note": "Forecast fallback active (warnings remain strictly sourced from IMD).",
                "forecast": points,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        except IntegrationError as exc:
            return {
                "status": "error",
                "source": "OpenWeatherMap",
                "note": exc.message,
                "forecast": [],
                "updated_at": None,
            }
