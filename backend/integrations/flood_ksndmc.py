"""Karnataka State Natural Disaster Monitoring Centre (KSNDMC) flood & reservoir release adapter."""

from datetime import datetime, timezone
from typing import Any, Dict, List

from config import get_settings
from integrations.base import BaseIntegrationClient, IntegrationError


class KsndmcFloodAdapter(BaseIntegrationClient):
    """
    Adapter for Karnataka State Natural Disaster Monitoring Centre (https://ksndmc.karnataka.gov.in).
    Public REST feeds are not open self-service APIs; reports honest not_configured status unless an official feed URL is configured.
    """

    service_name = "ksndmc_flood"

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.KSNDMC_FLOOD_API_URL or "",
            timeout_seconds=10.0,
            max_retries=1,
            cache_ttl_seconds=600,
        )
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.KSNDMC_FLOOD_API_URL)

    async def fetch_karnataka_alerts(self, state: str, district: str) -> Dict[str, Any]:
        if "karnataka" not in (state or "").strip().lower():
            return {
                "status": "not_applicable",
                "source": "KSNDMC (ksndmc.karnataka.gov.in)",
                "note": "KSNDMC covers Karnataka districts; refer to your state SDMA portal.",
                "advisories": [],
                "updated_at": None,
            }

        if not self.is_configured:
            return {
                "status": "not_configured",
                "source": "KSNDMC (ksndmc.karnataka.gov.in)",
                "note": (
                    "KSNDMC_FLOOD_API_URL not configured. Check https://ksndmc.karnataka.gov.in "
                    "for official Karnataka Varuna Mitra / reservoir release bulletins. Never fabricates flood warnings."
                ),
                "advisories": [],
                "updated_at": None,
            }

        headers = {}
        if self.settings.KSNDMC_API_KEY:
            headers["Authorization"] = f"Bearer {self.settings.KSNDMC_API_KEY}"

        try:
            data = await self.request_json(
                "GET",
                self.settings.KSNDMC_FLOOD_API_URL,
                params={"district": district},
                headers=headers,
                cache_key=f"ksndmc:{district.lower()}",
            )
            items = data if isinstance(data, list) else data.get("alerts", data.get("data", []))
            advisories: List[Dict[str, Any]] = [
                {
                    "station": str(item.get("station") or item.get("reservoir") or district),
                    "river": str(item.get("river") or item.get("basin") or "Karnataka Basin"),
                    "level_m": item.get("level_m"),
                    "danger_level_m": item.get("danger_level_m"),
                    "status": str(item.get("status") or item.get("alert_level") or "Official KSNDMC Advisory"),
                    "source": "KSNDMC Official Feed",
                    "updated_at": item.get("updated_at"),
                }
                for item in (items or [])
            ]
            return {
                "status": "configured",
                "source": "KSNDMC Official Feed",
                "note": "Live KSNDMC flood/reservoir alert feed.",
                "advisories": advisories,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        except IntegrationError as exc:
            return {
                "status": "error",
                "source": "KSNDMC Official Feed",
                "note": exc.message,
                "advisories": [],
                "updated_at": None,
            }
