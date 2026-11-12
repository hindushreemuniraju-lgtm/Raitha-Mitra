"""Central Water Commission (CWC) flood monitoring adapter."""

from datetime import datetime, timezone
from typing import Any, Dict, List

from config import get_settings
from integrations.base import BaseIntegrationClient, IntegrationError


class CwcFloodAdapter(BaseIntegrationClient):
    """
    Adapter for Central Water Commission flood data.
    ffs.india-water.gov.in is a web portal without a public self-service REST API;
    an official institutional feed URL (CWC_API_URL) must be configured for live data.
    """

    service_name = "cwc_flood"

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.CWC_API_URL or "",
            timeout_seconds=10.0,
            max_retries=1,
            cache_ttl_seconds=600,
        )
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.CWC_API_URL)

    async def fetch_flood_advisories(self, state: str, district: str) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "status": "unavailable",
                "source": "Central Water Commission (ffs.india-water.gov.in)",
                "note": (
                    "CWC has no public self-service REST API. Configure CWC_API_URL with official "
                    "institutional access, or check https://ffs.india-water.gov.in directly."
                ),
                "advisories": [],
                "updated_at": None,
            }

        headers = {}
        if self.settings.CWC_API_KEY:
            headers["Authorization"] = f"Bearer {self.settings.CWC_API_KEY}"

        try:
            data = await self.request_json(
                "GET",
                self.settings.CWC_API_URL,
                params={"state": state, "district": district},
                headers=headers,
                cache_key=f"cwc:{state.lower()}:{district.lower()}",
            )
            stations = data if isinstance(data, list) else data.get("stations", [])
            advisories: List[Dict[str, Any]] = [
                {
                    "station": str(s.get("station_name") or s.get("station") or "Station"),
                    "river": str(s.get("river") or "Unknown river"),
                    "level_m": s.get("water_level_m"),
                    "danger_level_m": s.get("danger_level_m"),
                    "status": str(s.get("status") or "Monitored"),
                    "source": "CWC Feed",
                    "updated_at": s.get("updated_at"),
                }
                for s in stations
            ]
            return {
                "status": "configured",
                "source": "CWC Institutional Feed",
                "note": "Live CWC river gauge feed.",
                "advisories": advisories,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        except IntegrationError as exc:
            return {
                "status": "error",
                "source": "CWC Institutional Feed",
                "note": exc.message,
                "advisories": [],
                "updated_at": None,
            }
