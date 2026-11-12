"""Pluggable fallback vision model adapter interface for crop disease diagnosis."""

import base64
import json
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_settings
from integrations.base import BaseIntegrationClient, IntegrationError


class DiseaseVisionFallbackAdapter(BaseIntegrationClient):
    """
    Pluggable multimodal vision adapter (OpenAI-compatible /v1/chat/completions)
    used only when Plantix is unconfigured and VISION_MODEL_* env vars are supplied.
    """

    service_name = "vision_fallback"

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url=settings.VISION_MODEL_BASE_URL or "",
            timeout_seconds=20.0,
            max_retries=1,
            cache_ttl_seconds=0,
        )
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(
            self.settings.VISION_MODEL_BASE_URL
            and self.settings.VISION_MODEL_API_KEY
            and self.settings.VISION_MODEL_NAME
        )

    async def analyze_image(
        self, image_path: Path, *, crop_name: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.is_configured:
            return {"status": "not_configured", "adapter": "vision_fallback"}

        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        ext = image_path.suffix.lstrip(".").lower() or "jpeg"
        if ext == "jpg":
            ext = "jpeg"

        prompt = (
            "Analyze this crop plant image strictly as JSON with keys: "
            "diagnosis_name (string), confidence (0.0-1.0 float), symptoms (list of strings), "
            "organic_treatments (list), chemical_treatments (list), precautions (list). "
            f"Crop hint: {crop_name or 'unknown'}. If image is unclear, set confidence < 0.5."
        )

        body = {
            "model": self.settings.VISION_MODEL_NAME,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/{ext};base64,{encoded}"},
                        },
                    ],
                }
            ],
            "temperature": 0.1,
        }

        try:
            payload = await self.request_json(
                "POST",
                "/chat/completions",
                json_body=body,
                headers={"Authorization": f"Bearer {self.settings.VISION_MODEL_API_KEY}"},
            )
            raw_text = payload["choices"][0]["message"]["content"]
            parsed = json.loads(raw_text)
            conf = float(parsed.get("confidence", 0.0))
            return {
                "status": "diagnosed" if conf >= 0.65 else "uncertain",
                "adapter": f"vision_fallback:{self.settings.VISION_MODEL_NAME}",
                "confidence": round(conf, 3),
                "diagnosis_name": parsed.get("diagnosis_name", "Uncertain"),
                "symptoms": parsed.get("symptoms", []),
                "organic_treatments": parsed.get("organic_treatments", []),
                "chemical_treatments": parsed.get("chemical_treatments", []),
                "precautions": parsed.get("precautions", []),
                "raw_summary": raw_text[:500],
            }
        except (IntegrationError, KeyError, IndexError, ValueError, TypeError) as exc:
            return {
                "status": "error",
                "adapter": "vision_fallback",
                "raw_summary": str(exc),
            }
