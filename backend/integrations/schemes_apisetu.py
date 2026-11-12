"""API Setu myScheme integration adapter."""

from typing import Any, Dict

from config import get_settings
from integrations.base import BaseIntegrationClient, IntegrationError


class ApiSetuMySchemeAdapter(BaseIntegrationClient):
    """Adapter for https://apisetu.gov.in/dic/myscheme directory endpoints."""

    service_name = "apisetu_myscheme"

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url="https://apisetu.gov.in/dic/myscheme",
            timeout_seconds=10.0,
            max_retries=1,
            cache_ttl_seconds=3600,
        )
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.APISETU_API_KEY and self.settings.APISETU_CLIENT_ID)

    async def check_gateway_health(self) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "status": "not_configured",
                "note": "APISETU_API_KEY and APISETU_CLIENT_ID not configured.",
            }
        try:
            await self.request_json(
                "GET",
                "/v1/schemes",
                headers={
                    "X-APISETU-APIKEY": self.settings.APISETU_API_KEY,
                    "X-APISETU-CLIENTID": self.settings.APISETU_CLIENT_ID,
                },
                cache_key="apisetu:health",
            )
            return {"status": "configured", "note": "API Setu myScheme connected."}
        except IntegrationError as exc:
            return {"status": "error", "note": exc.message}
