"""data.gov.in AGMARKNET daily commodity price adapter."""

from typing import Any, Dict, List, Optional

from config import get_settings
from integrations.base import BaseIntegrationClient, IntegrationError


AGMARKNET_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"


class AgmarknetDataGovAdapter(BaseIntegrationClient):
    """Queries Open Government Data India AGMARKNET daily prices API."""

    service_name = "data_gov_in_agmarknet"

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url="https://api.data.gov.in",
            timeout_seconds=12.0,
            max_retries=2,
            cache_ttl_seconds=1800,
        )
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.DATA_GOV_IN_API_KEY)

    async def fetch_daily_prices(
        self,
        *,
        commodity: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None,
        limit: int = 30,
    ) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "status": "not_configured",
                "note": "DATA_GOV_IN_API_KEY not configured.",
                "records": [],
            }

        params: Dict[str, Any] = {
            "api-key": self.settings.DATA_GOV_IN_API_KEY,
            "format": "json",
            "limit": limit,
        }
        if state:
            params["filters[state]"] = state
        if district:
            params["filters[district]"] = district
        if commodity:
            params["filters[commodity]"] = commodity
        if market:
            params["filters[market]"] = market

        cache_key = f"agm:{state or ''}:{district or ''}:{commodity or ''}:{market or ''}"
        try:
            payload = await self.request_json(
                "GET",
                f"/resource/{AGMARKNET_RESOURCE_ID}",
                params=params,
                cache_key=cache_key,
            )
            rows: List[Dict[str, Any]] = []
            for rec in payload.get("records", []):
                try:
                    rows.append(
                        {
                            "state": str(rec.get("state") or ""),
                            "district": str(rec.get("district") or ""),
                            "market": str(rec.get("market") or ""),
                            "commodity": str(rec.get("commodity") or ""),
                            "variety": str(rec.get("variety") or "Standard"),
                            "min_price_inr": float(rec.get("min_price") or 0),
                            "max_price_inr": float(rec.get("max_price") or 0),
                            "modal_price_inr": float(rec.get("modal_price") or 0),
                            "arrivals_tonnes": None,
                            "price_date": str(rec.get("arrival_date") or ""),
                            "source": "AGMARKNET (data.gov.in)",
                        }
                    )
                except (ValueError, TypeError):
                    continue
            return {
                "status": "configured",
                "note": "Latest available daily data from data.gov.in AGMARKNET.",
                "records": rows,
            }
        except IntegrationError as exc:
            return {
                "status": "error",
                "note": exc.message,
                "records": [],
            }
