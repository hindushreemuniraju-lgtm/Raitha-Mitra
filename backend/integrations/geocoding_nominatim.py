"""OpenStreetMap Nominatim reverse & forward geocoding adapter."""

from typing import Any, Dict, Optional

from config import get_settings
from integrations.base import BaseIntegrationClient, IntegrationError


class NominatimGeocodingAdapter(BaseIntegrationClient):
    """Reverse-geocode farm coordinates into village, taluk, district, and state."""

    service_name = "nominatim_geocoding"

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url="https://nominatim.openstreetmap.org",
            timeout_seconds=8.0,
            max_retries=2,
            cache_ttl_seconds=3600,
        )
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return True

    async def reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, Any]:
        headers = {
            "User-Agent": self.settings.NOMINATIM_USER_AGENT,
            "Accept-Language": "en",
        }
        try:
            data = await self.request_json(
                "GET",
                "/reverse",
                params={
                    "lat": round(latitude, 6),
                    "lon": round(longitude, 6),
                    "format": "json",
                    "addressdetails": 1,
                },
                headers=headers,
                cache_key=f"nominatim:rev:{latitude:.4f}:{longitude:.4f}",
                cache_ttl=3600,
            )
            addr = data.get("address") or {}
            village = str(
                addr.get("village")
                or addr.get("hamlet")
                or addr.get("suburb")
                or addr.get("neighbourhood")
                or addr.get("town")
                or addr.get("city")
                or ""
            ).strip()
            taluk = str(
                addr.get("county")
                or addr.get("subdistrict")
                or addr.get("municipality")
                or addr.get("town")
                or ""
            ).strip()
            district = str(
                addr.get("state_district")
                or addr.get("county")
                or addr.get("city_district")
                or addr.get("city")
                or ""
            ).strip()
            # Clean "Mandya district" suffix when present
            if district.lower().endswith(" district"):
                district = district[:-9].strip()
            if taluk.lower().endswith(" taluk") or taluk.lower().endswith(" taluka"):
                taluk = taluk.rsplit(" ", 1)[0].strip()

            state = str(addr.get("state") or "").strip()
            display_name = str(data.get("display_name") or "").strip()

            return {
                "status": "ok",
                "latitude": round(latitude, 6),
                "longitude": round(longitude, 6),
                "village": village,
                "taluk": taluk,
                "district": district,
                "state": state,
                "display_name": display_name or ", ".join(p for p in [village, taluk, district, state] if p),
                "source": "OpenStreetMap Nominatim",
            }
        except IntegrationError as exc:
            return {
                "status": "unavailable",
                "latitude": round(latitude, 6),
                "longitude": round(longitude, 6),
                "village": "",
                "taluk": "",
                "district": "",
                "state": "",
                "display_name": f"{latitude:.5f}, {longitude:.5f}",
                "source": f"Nominatim unavailable: {exc.message}",
            }

    async def forward_geocode(self, query: str) -> Optional[Dict[str, float]]:
        if not query or not query.strip():
            return None
        headers = {"User-Agent": self.settings.NOMINATIM_USER_AGENT}
        try:
            data = await self.request_json(
                "GET",
                "/search",
                params={"q": query.strip(), "format": "json", "limit": 1},
                headers=headers,
                cache_key=f"nominatim:fwd:{query.strip().lower()}",
                cache_ttl=86400,
            )
            if isinstance(data, list) and data:
                return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}
        except IntegrationError:
            return None
        return None
