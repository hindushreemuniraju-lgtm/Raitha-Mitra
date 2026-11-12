"""USDA FoodData Central API adapter."""

from typing import Any, Dict, List

from config import get_settings
from integrations.base import BaseIntegrationClient, IntegrationError


class UsdaFoodDataAdapter(BaseIntegrationClient):
    """Queries https://api.nal.usda.gov/fdc/v1/foods/search for verified composition data."""

    service_name = "usda_fdc"

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url="https://api.nal.usda.gov/fdc/v1",
            timeout_seconds=10.0,
            max_retries=2,
            cache_ttl_seconds=86400,
        )
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.USDA_FDC_API_KEY)

    async def search_food(self, query: str, page_size: int = 3) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "status": "not_configured",
                "results": [],
            }

        try:
            payload = await self.request_json(
                "GET",
                "/foods/search",
                params={
                    "api_key": self.settings.USDA_FDC_API_KEY,
                    "query": query,
                    "dataType": "Foundation,SR Legacy",
                    "pageSize": page_size,
                },
                cache_key=f"usda:{query.lower()}:{page_size}",
            )
            results: List[Dict[str, Any]] = []
            for food in payload.get("foods", [])[:page_size]:
                nutrients = [
                    {
                        "name": n.get("nutrientName"),
                        "value": n.get("value"),
                        "unit": n.get("unitName"),
                    }
                    for n in (food.get("foodNutrients") or [])[:10]
                    if n.get("value") is not None
                ]
                results.append(
                    {
                        "fdc_id": food.get("fdcId"),
                        "description": food.get("description"),
                        "data_type": food.get("dataType"),
                        "nutrients": nutrients,
                    }
                )
            return {"status": "configured", "results": results}
        except IntegrationError:
            return {"status": "error", "results": []}
