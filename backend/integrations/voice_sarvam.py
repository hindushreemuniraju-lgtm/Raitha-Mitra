"""Sarvam AI REST adapter (Saaras STT, Sarvam-105b Chat, Bulbul TTS)."""

from typing import Any, Dict, List, Optional

import httpx

from config import get_settings
from integrations.base import BaseIntegrationClient, IntegrationError


LANGUAGE_SPEAKERS: Dict[str, str] = {
    "kn-IN": "anushka",
    "hi-IN": "anant",
    "te-IN": "anushka",
    "en-IN": "anushka",
    "ta-IN": "anushka",
    "mr-IN": "anant",
}

LANGUAGE_NAMES: Dict[str, str] = {
    "kn-IN": "Kannada (ಕನ್ನಡ)",
    "hi-IN": "Hindi (हिन्दी)",
    "te-IN": "Telugu (తెలుగు)",
    "en-IN": "English",
    "ta-IN": "Tamil (தமிழ்)",
    "mr-IN": "Marathi (मराठी)",
}


class SarvamAiAdapter(BaseIntegrationClient):
    """Direct REST integration with https://api.sarvam.ai for STT, LLM, and TTS."""

    service_name = "sarvam_ai"

    def __init__(self):
        settings = get_settings()
        super().__init__(
            base_url="https://api.sarvam.ai",
            timeout_seconds=20.0,
            max_retries=1,
            cache_ttl_seconds=0,
        )
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.SARVAM_API_KEY)

    def _headers(self) -> Dict[str, str]:
        return {"api-subscription-key": self.settings.SARVAM_API_KEY}

    async def transcribe_audio(
        self, audio_bytes: bytes, filename: str, language_code: str
    ) -> Dict[str, Any]:
        if not self.is_configured:
            return {"status": "not_configured", "transcript": ""}

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    "https://api.sarvam.ai/speech-to-text",
                    headers=self._headers(),
                    files={"file": (filename, audio_bytes, "audio/webm")},
                    data={
                        "model": self.settings.SARVAM_STT_MODEL,
                        "language_code": language_code,
                        "mode": "transcribe",
                    },
                )
            if resp.status_code >= 400:
                return {
                    "status": "error",
                    "transcript": "",
                    "note": f"Sarvam STT returned HTTP {resp.status_code}.",
                }
            data = resp.json()
            return {
                "status": "configured",
                "transcript": str(data.get("transcript") or ""),
            }
        except Exception as exc:
            return {"status": "error", "transcript": "", "note": type(exc).__name__}

    async def generate_chat_reply(
        self,
        *,
        system_prompt: str,
        history: List[Dict[str, str]],
        user_message: str,
    ) -> Dict[str, Any]:
        if not self.is_configured:
            return {"status": "not_configured", "reply": ""}

        messages = [{"role": "system", "content": system_prompt}, *history, {"role": "user", "content": user_message}]
        try:
            payload = await self.request_json(
                "POST",
                "/v2/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.SARVAM_API_KEY}",
                    "api-subscription-key": self.settings.SARVAM_API_KEY,
                },
                json_body={
                    "model": self.settings.SARVAM_LLM_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 350,
                },
            )
            content = payload["choices"][0]["message"]["content"]
            return {"status": "configured", "reply": str(content).strip()}
        except (IntegrationError, KeyError, IndexError, TypeError) as exc:
            return {"status": "error", "reply": "", "note": str(exc)}

    async def synthesize_speech(
        self, text: str, language_code: str
    ) -> Dict[str, Any]:
        if not self.is_configured or not text.strip():
            return {"status": "not_configured", "audio_base64": None}

        speaker = LANGUAGE_SPEAKERS.get(language_code, "anushka")
        try:
            payload = await self.request_json(
                "POST",
                "/text-to-speech",
                headers=self._headers(),
                json_body={
                    "inputs": [text[:500]],
                    "target_language_code": language_code,
                    "speaker": speaker,
                    "model": self.settings.SARVAM_TTS_MODEL,
                    "speech_sample_rate": 22050,
                    "enable_preprocessing": True,
                },
            )
            audios = payload.get("audios") or []
            return {
                "status": "configured",
                "audio_base64": audios[0] if audios else None,
                "audio_mime": "audio/wav",
            }
        except IntegrationError as exc:
            return {"status": "error", "audio_base64": None, "note": exc.message}
