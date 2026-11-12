"""Plantix Intelligence B2B Crop Health API adapter (b2b.plantix.net Stoplight spec)."""

from pathlib import Path
from typing import Any, Dict, Optional

from config import get_settings
from integrations.base import BaseIntegrationClient, IntegrationError


class PlantixAdapter(BaseIntegrationClient):
    """
    Dedicated adapter for Plantix Intelligence B2B API (`POST /v1/image-analysis`).
    Requires commercial B2B partner approval and configured PLANTIX_BASE_URL + PLANTIX_API_KEY.
    """

    service_name = "plantix"

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.PLANTIX_BASE_URL or "",
            timeout_seconds=15.0,
            max_retries=1,
            cache_ttl_seconds=0,
        )
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.PLANTIX_BASE_URL and self.settings.PLANTIX_API_KEY)

    async def analyze_image(
        self,
        image_path: Path,
        *,
        crop_name: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        farmer_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not self.is_configured:
            return {"status": "not_configured", "adapter": "plantix"}

        form_data: Dict[str, Any] = {}
        if crop_name:
            form_data["crop"] = crop_name.strip().lower().replace(" ", "_")
        if latitude is not None:
            form_data["latitude"] = str(latitude)
        if longitude is not None:
            form_data["longitude"] = str(longitude)
        if farmer_id is not None:
            form_data["application_end_user_id"] = f"farmer_{farmer_id}"

        image_bytes = image_path.read_bytes()
        files = {"image": (image_path.name, image_bytes, "application/octet-stream")}
        headers = {"Authorization": f"Bearer {self.settings.PLANTIX_API_KEY}"}

        try:
            payload = await self.request_json(
                "POST",
                "/v1/image-analysis",
                data=form_data,
                files=files,
                headers=headers,
            )
            predictions = payload.get("predicted_diagnoses") or payload.get("diagnoses") or []
            if not predictions:
                return {
                    "status": "uncertain",
                    "adapter": "plantix",
                    "confidence": 0.0,
                    "diagnosis_name": "Inconclusive leaf image",
                    "symptoms": [],
                    "organic_treatments": [],
                    "chemical_treatments": [],
                    "precautions": [
                        "Capture a sharp close-up of the affected leaf in natural daylight and upload again."
                    ],
                    "raw_summary": "Plantix returned no confident diagnosis.",
                }
            top = predictions[0]
            confidence = float(top.get("likelihood") or top.get("confidence") or 0.0)
            return {
                "status": "diagnosed" if confidence >= 0.65 else "uncertain",
                "adapter": "plantix",
                "confidence": round(confidence, 3),
                "diagnosis_name": str(top.get("common_name") or top.get("name") or "Detected condition"),
                "symptoms": list(top.get("symptoms") or []),
                "organic_treatments": list(top.get("organic_treatment") or top.get("organic_treatments") or []),
                "chemical_treatments": list(top.get("chemical_treatment") or top.get("chemical_treatments") or []),
                "precautions": list(top.get("preventive_measures") or top.get("precautions") or []),
                "raw_summary": str(top.get("description") or ""),
            }
        except IntegrationError as exc:
            return {
                "status": "error",
                "adapter": "plantix",
                "raw_summary": exc.message,
            }
