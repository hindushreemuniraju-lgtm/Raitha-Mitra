"""India Meteorological Department (IMD) weather warnings and forecast adapter."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config import get_settings
from integrations.base import BaseIntegrationClient, IntegrationError


class ImdWeatherAdapter(BaseIntegrationClient):
    """
    Adapter for official IMD API Management Platform (https://api.imd.gov.in).
    Requires institutional/developer registration, static IP whitelisting, and API key/JWT.
    """

    service_name = "imd_weather"

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.IMD_API_BASE_URL,
            timeout_seconds=10.0,
            max_retries=2,
            cache_ttl_seconds=600,
        )
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.IMD_API_KEY or (self.settings.IMD_USERNAME and self.settings.IMD_PASSWORD))

    async def _get_bearer_token(self) -> Optional[str]:
        if not (self.settings.IMD_USERNAME and self.settings.IMD_PASSWORD):
            return None
        try:
            payload = await self.request_json(
                "POST",
                "/api/oauth/token.php",
                json_body={
                    "username": self.settings.IMD_USERNAME,
                    "password": self.settings.IMD_PASSWORD,
                },
                cache_key="imd:oauth_token",
                cache_ttl=1800,
            )
            return payload.get("access_token") or payload.get("token")
        except IntegrationError:
            return None

    async def fetch_district_warnings(self, state: str, district: str) -> Dict[str, Any]:
        """Fetch official IMD warnings; returns honest not_configured if credentials are absent."""
        if not self.is_configured:
            return {
                "status": "not_configured",
                "source": "IMD (api.imd.gov.in)",
                "note": "IMD credentials (IMD_API_KEY / IMD_USERNAME) not configured. No synthetic alerts generated.",
                "warnings": [],
                "updated_at": None,
            }

        headers: Dict[str, str] = {}
        if self.settings.IMD_API_KEY:
            headers["X-API-KEY"] = self.settings.IMD_API_KEY
        token = await self._get_bearer_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            data = await self.request_json(
                "GET",
                self.settings.IMD_WARNINGS_PATH,
                params={"state": state, "district": district},
                headers=headers,
                cache_key=f"imd:warn:{state.lower()}:{district.lower()}",
                cache_ttl=600,
            )
            raw_items = data if isinstance(data, list) else data.get("warnings", data.get("data", []))
            warnings: List[Dict[str, Any]] = []
            for item in raw_items or []:
                color = str(item.get("color", item.get("warning_color", "green"))).lower()
                severity = color if color in {"green", "yellow", "orange", "red"} else "yellow"
                warnings.append(
                    {
                        "severity": severity,
                        "title": str(item.get("title") or item.get("warning") or "IMD District Advisory"),
                        "description": str(item.get("description") or item.get("message") or ""),
                        "source": "IMD Official API",
                        "issued_at": item.get("issued_at") or item.get("date"),
                    }
                )
            return {
                "status": "configured",
                "source": "IMD Official API (api.imd.gov.in)",
                "note": "Live IMD district warning feed.",
                "warnings": warnings,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        except IntegrationError as exc:
            return {
                "status": "error",
                "source": "IMD Official API (api.imd.gov.in)",
                "note": exc.message,
                "warnings": [],
                "updated_at": None,
            }
