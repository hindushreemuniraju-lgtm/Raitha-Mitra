"""CEDA Ashoka University Agmarknet API adapter."""

from typing import Any, Dict, List, Optional

from config import get_settings
from integrations.base import BaseIntegrationClient, IntegrationError


class CedaAgmarknetAdapter(BaseIntegrationClient):
    """Queries https://api.ceda.ashoka.edu.in/v1 for cleaned Agmarknet prices & arrivals."""

    service_name = "ceda_agmarknet"

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url="https://api.ceda.ashoka.edu.in/v1",
            timeout_seconds=12.0,
            max_retries=1,
            cache_ttl_seconds=1800,
        )
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.CEDA_API_KEY)

    def _headers(self) -> Dict[str, str]:
        if self.settings.CEDA_AUTH_HEADER.lower() == "authorization":
            return {"Authorization": f"Bearer {self.settings.CEDA_API_KEY}"}
        return {self.settings.CEDA_AUTH_HEADER: self.settings.CEDA_API_KEY}

    async def fetch_prices(
        self,
        *,
        commodity_id: Optional[str] = None,
        state_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "status": "not_configured",
                "note": "CEDA_API_KEY not configured.",
                "records": [],
            }

        body: Dict[str, Any] = {}
        if commodity_id:
            body["commodity_id"] = commodity_id
        if state_id:
            body["state_id"] = state_id
        if start_date:
            body["start_date"] = start_date
        if end_date:
            body["end_date"] = end_date

        try:
            payload = await self.request_json(
                "POST",
                "/agmarknet/prices",
                json_body=body,
                headers=self._headers(),
                cache_key=f"ceda:{commodity_id or ''}:{state_id or ''}:{start_date or ''}",
            )
            raw_list = payload.get("data", payload.get("records", [])) if isinstance(payload, dict) else []
            rows: List[Dict[str, Any]] = []
            for rec in raw_list[:30]:
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
                        "arrivals_tonnes": rec.get("arrivals") or rec.get("quantity"),
                        "price_date": str(rec.get("date") or ""),
                        "source": "CEDA Agmarknet",
                    }
                )
            return {"status": "configured", "note": "CEDA Agmarknet daily feed.", "records": rows}
        except IntegrationError as exc:
            return {"status": "error", "note": exc.message, "records": []}
