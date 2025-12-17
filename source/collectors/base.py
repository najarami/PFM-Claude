"""Base collector class for API data fetching."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional
from datetime import datetime

import httpx

from source.config import settings

logger = logging.getLogger(__name__)


class CollectorError(Exception):
    """Base exception for collector errors."""


class RateLimitError(CollectorError):
    """Rate limit exceeded."""


class APIError(CollectorError):
    """API returned an error."""


class BaseCollector(ABC):
    """Base class for all data collectors."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        rate_limit_rpm: int = 30,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.rate_limit_rpm = rate_limit_rpm
        self._last_request_time: Optional[datetime] = None
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        if self._last_request_time is None:
            self._last_request_time = datetime.now()
            return

        min_interval = 60.0 / self.rate_limit_rpm
        elapsed = (datetime.now() - self._last_request_time).total_seconds()

        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)

        self._last_request_time = datetime.now()

    async def _request(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make an HTTP request with retry logic."""
        await self._rate_limit()

        url = f"{self.base_url}{endpoint}"
        request_headers = headers or {}

        if self.api_key:
            request_headers["Authorization"] = f"Bearer {self.api_key}"

        client = await self._get_client()

        for attempt in range(settings.max_retries):
            try:
                response = await client.get(
                    url,
                    params=params,
                    headers=request_headers,
                )

                if response.status_code == 429:
                    wait_time = settings.retry_backoff * (2**attempt)
                    logger.warning(
                        f"Rate limited, waiting {wait_time}s (attempt {attempt + 1})"
                    )
                    await asyncio.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                if attempt == settings.max_retries - 1:
                    raise APIError(f"API error: {e.response.status_code}")
                await asyncio.sleep(settings.retry_backoff * (2**attempt))

            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                if attempt == settings.max_retries - 1:
                    raise CollectorError(f"Request failed: {e}")
                await asyncio.sleep(settings.retry_backoff * (2**attempt))

        raise CollectorError("Max retries exceeded")

    @abstractmethod
    async def fetch(self) -> dict[str, Any]:
        """Fetch data from the API. Must be implemented by subclasses."""

    @abstractmethod
    def parse(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Parse raw API response into structured data."""

    def validate(self, data: dict[str, Any]) -> bool:
        """Validate parsed data. Override in subclasses for custom validation."""
        return True

    async def collect(self) -> dict[str, Any]:
        """Full collection pipeline: fetch, parse, validate."""
        try:
            raw_data = await self.fetch()
            parsed_data = self.parse(raw_data)

            if not self.validate(parsed_data):
                raise CollectorError("Data validation failed")

            return parsed_data

        except Exception as e:
            logger.error(f"Collection failed for {self.__class__.__name__}: {e}")
            raise
