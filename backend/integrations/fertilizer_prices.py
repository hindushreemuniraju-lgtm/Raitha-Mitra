"""Verified fertilizer MRP / price feed adapter (never hardcodes unverified prices)."""

from typing import Any, Dict

from config import get_settings
from integrations.base import BaseIntegrationClient, IntegrationError


class FertilizerPriceAdapter(BaseIntegrationClient):
    """Fetches fertilizer prices only from a configured verified source with verification date."""

    service_name = "fertilizer_prices"

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.FERTILIZER_PRICE_API_URL or "",
            timeout_seconds=8.0,
            max_retries=1,
            cache_ttl_seconds=3600,
        )
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.FERTILIZER_PRICE_API_URL)

    async def get_price(self, product_name: str, state: str) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "price_inr": None,
                "price_status": "unavailable",
                "price_source": None,
                "price_verified_date": None,
            }

        headers = {}
        if self.settings.FERTILIZER_PRICE_API_KEY:
            headers["Authorization"] = f"Bearer {self.settings.FERTILIZER_PRICE_API_KEY}"

        try:
            data = await self.request_json(
                "GET",
                self.settings.FERTILIZER_PRICE_API_URL,
                params={"product": product_name, "state": state},
                headers=headers,
                cache_key=f"fert_price:{state.lower()}:{product_name.lower()}",
            )
            return {
                "price_inr": data.get("price_inr"),
                "price_status": "verified" if data.get("price_inr") is not None else "unavailable",
                "price_source": data.get("source"),
                "price_verified_date": data.get("verified_date"),
            }
        except IntegrationError:
            return {
                "price_inr": None,
                "price_status": "unavailable",
                "price_source": None,
                "price_verified_date": None,
            }
