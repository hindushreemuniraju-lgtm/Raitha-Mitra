"""Base HTTP integration client with timeouts, retries, rate-limit handling, caching, and validation."""

import asyncio
import logging
from typing import Any, Dict, Optional, Type, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from utils.cache import shared_cache


logger = logging.getLogger("raitha_mitra.integrations")
T = TypeVar("T", bound=BaseModel)


class IntegrationError(Exception):
    """Structured error raised by external integration adapters."""

    def __init__(self, service: str, code: str, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.service = service
        self.code = code
        self.message = message
        self.status_code = status_code


class BaseIntegrationClient:
    """Shared resilient HTTP adapter base for all external APIs."""

    service_name: str = "external_api"

    def __init__(
        self,
        base_url: str = "",
        timeout_seconds: float = 10.0,
        max_retries: int = 2,
        cache_ttl_seconds: int = 300,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.cache_ttl_seconds = cache_ttl_seconds

    async def request_json(
        self,
        method: str,
        url_or_path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        cache_key: Optional[str] = None,
        cache_ttl: Optional[int] = None,
        response_model: Optional[Type[T]] = None,
    ) -> Any:
        """Execute an HTTP request with caching, retries, rate-limit handling, and validation."""
        if cache_key:
            cached = shared_cache.get(cache_key)
            if cached is not None:
                return cached

        url = (
            url_or_path
            if url_or_path.startswith("http://") or url_or_path.startswith("https://")
            else f"{self.base_url}/{url_or_path.lstrip('/')}"
        )

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.request(
                        method=method.upper(),
                        url=url,
                        params=params,
                        json=json_body,
                        data=data,
                        files=files,
                        headers=headers,
                    )

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "2") or "2")
                    if attempt < self.max_retries:
                        await asyncio.sleep(min(retry_after, 5))
                        continue
                    raise IntegrationError(
                        self.service_name,
                        "rate_limited",
                        f"{self.service_name} rate limit reached (HTTP 429).",
                        status_code=429,
                    )

                if response.status_code >= 500:
                    if attempt < self.max_retries:
                        await asyncio.sleep(0.5 * (2**attempt))
                        continue
                    raise IntegrationError(
                        self.service_name,
                        "upstream_error",
                        f"{self.service_name} returned server error HTTP {response.status_code}.",
                        status_code=response.status_code,
                    )

                if response.status_code >= 400:
                    raise IntegrationError(
                        self.service_name,
                        "request_rejected",
                        f"{self.service_name} rejected request with HTTP {response.status_code}.",
                        status_code=response.status_code,
                    )

                payload = response.json()
                if response_model is not None:
                    try:
                        validated = response_model.model_validate(payload)
                        payload = validated.model_dump()
                    except ValidationError as exc:
                        raise IntegrationError(
                            self.service_name,
                            "invalid_response",
                            f"{self.service_name} response failed schema validation.",
                        ) from exc

                if cache_key:
                    shared_cache.set(
                        cache_key,
                        payload,
                        ttl_seconds=cache_ttl if cache_ttl is not None else self.cache_ttl_seconds,
                    )
                return payload

            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as exc:
                last_error = exc
                logger.warning(
                    "%s transient network error on attempt %d: %s",
                    self.service_name,
                    attempt + 1,
                    type(exc).__name__,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                raise IntegrationError(
                    self.service_name,
                    "network_unavailable",
                    f"Unable to reach {self.service_name}: {type(exc).__name__}",
                ) from exc
            except ValueError as exc:
                raise IntegrationError(
                    self.service_name,
                    "invalid_json",
                    f"{self.service_name} returned non-JSON response.",
                ) from exc

        raise IntegrationError(
            self.service_name,
            "unknown_error",
            f"{self.service_name} failed after retries: {last_error}",
        )
