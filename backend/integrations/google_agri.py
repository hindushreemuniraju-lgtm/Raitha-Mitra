"""Google Agricultural Understanding Platform (ALU / AMED) adapter."""

from typing import Any, Dict, Optional

from config import get_settings
from integrations.base import BaseIntegrationClient, IntegrationError


class GoogleAgriAdapter(BaseIntegrationClient):
    """
    Adapter for Google's Agricultural Understanding Platform:
    https://agriculturalunderstanding.googleapis.com
    Note: ALU/AMED provides field boundaries, irrigation structures, likely crop, and
    sowing/harvest dates. It does NOT provide a yield prediction endpoint.
    """

    service_name = "google_agri"

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url="https://agriculturalunderstanding.googleapis.com",
            timeout_seconds=12.0,
            max_retries=1,
            cache_ttl_seconds=3600,
        )
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.GOOGLE_AGRI_API_KEY)

    async def lookup_landscape_metadata(
        self, latitude: Optional[float], longitude: Optional[float]
    ) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "status": "not_configured",
                "note": (
                    "GOOGLE_AGRI_API_KEY not configured. Note: Google ALU/AMED provides field boundaries "
                    "and sowing/harvest dates only—yield is computed by Raitha Mitra's modular agronomic engine."
                ),
                "metadata": None,
            }
        if latitude is None or longitude is None:
            return {
                "status": "not_configured",
                "note": "Opt-in GPS coordinates are required to query Google ALU/AMED S2 landscape cells.",
                "metadata": None,
            }

        try:
            payload = await self.request_json(
                "POST",
                "/v1:lookupLandscape",
                params={"key": self.settings.GOOGLE_AGRI_API_KEY},
                json_body={"location": {"latitude": latitude, "longitude": longitude}},
                cache_key=f"google_alu:{round(latitude, 3)}:{round(longitude, 3)}",
            )
            return {
                "status": "configured",
                "note": "Landscape metadata retrieved from Google Agricultural Understanding Platform (ALU/AMED).",
                "metadata": payload,
            }
        except IntegrationError as exc:
            return {
                "status": "error",
                "note": exc.message,
                "metadata": None,
            }
