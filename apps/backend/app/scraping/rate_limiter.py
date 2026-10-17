import asyncio
import time
from typing import Dict
from urllib.parse import urlparse

from app.core.config import settings
from app.core.logging import logger


class DomainRateLimiter:
    """
    Manages per-domain rate limiting and concurrency limits.
    Prevents overwhelming target web servers and respects crawl delays.
    """

    def __init__(
        self,
        max_concurrent_requests: int = 3,
        default_delay_seconds: float = 0.5,
    ):
        self.max_concurrent = max_concurrent_requests
        self.default_delay = default_delay_seconds
        self._semaphores: Dict[str, asyncio.Semaphore] = {}
        self._last_request_time: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    def _get_domain(self, url: str) -> str:
        return urlparse(url).netloc.lower()

    async def _get_semaphore(self, domain: str) -> asyncio.Semaphore:
        async with self._lock:
            if domain not in self._semaphores:
                self._semaphores[domain] = asyncio.Semaphore(self.max_concurrent)
            return self._semaphores[domain]

    async def acquire(self, url: str, custom_delay: float = None) -> None:
        """
        Wait for domain concurrency slot and enforces mandatory delay since last request.
        """
        domain = self._get_domain(url)
        semaphore = await self._get_semaphore(domain)
        await semaphore.acquire()

        delay = custom_delay if custom_delay is not None else self.default_delay
        now = time.time()
        last_time = self._last_request_time.get(domain, 0.0)
        time_since_last = now - last_time

        if time_since_last < delay:
            wait_needed = delay - time_since_last
            await asyncio.sleep(wait_needed)

        self._last_request_time[domain] = time.time()

    def release(self, url: str) -> None:
        """Releases domain concurrency slot."""
        domain = self._get_domain(url)
        if domain in self._semaphores:
            try:
                self._semaphores[domain].release()
            except ValueError:
                pass


rate_limiter = DomainRateLimiter(
    max_concurrent_requests=settings.SCRAPER_MAX_CONCURRENT_REQUESTS,
    default_delay_seconds=settings.SCRAPER_REQUEST_DELAY_SECONDS,
)
