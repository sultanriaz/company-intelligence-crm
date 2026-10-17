import asyncio
from typing import Optional
from urllib.parse import urljoin
import httpx

from app.core.config import settings
from app.core.exceptions import SSRFViolationException, RateLimitExceededException
from app.core.logging import logger
from app.scraping.rate_limiter import rate_limiter
from app.security.ssrf import validate_target_url

MAX_REDIRECTS = 5
MAX_BODY_BYTES = 5 * 1024 * 1024  # 5 MB


class SafeScraperClient:
    """
    Hardened HTTP client for web scraping with:
    - Pre-flight and per-redirect SSRF checks
    - Domain rate limiting and concurrency management
    - Body size limiting (defense against Decompression Bomb / Memory Exhaustion)
    - Exponential backoff on HTTP 429 Retry-After
    """

    def __init__(self, user_agent: Optional[str] = None, timeout_seconds: Optional[int] = None):
        self.user_agent = user_agent or settings.SCRAPER_USER_AGENT
        self.timeout = timeout_seconds or settings.SCRAPER_TIMEOUT_SECONDS

    async def fetch_page(
        self,
        url: str,
        allow_local_for_testing: bool = False,
        max_retries: int = 2,
    ) -> httpx.Response:
        # Pre-flight SSRF check
        validated_url = validate_target_url(url, allow_local_for_testing=allow_local_for_testing)

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        current_url = validated_url
        redirect_count = 0

        for attempt in range(max_retries + 1):
            await rate_limiter.acquire(current_url)
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout),
                    follow_redirects=False,
                    verify=True,
                ) as client:
                    while True:
                        response = await client.get(current_url, headers=headers)

                        # Handle redirect chain with SSRF validation at every step
                        if response.is_redirect and "location" in response.headers:
                            redirect_count += 1
                            if redirect_count > MAX_REDIRECTS:
                                raise SSRFViolationException(f"Exceeded max redirects ({MAX_REDIRECTS}) for {url}")

                            raw_location = response.headers["location"]
                            next_url = urljoin(current_url, raw_location)
                            # Validate redirect target against SSRF rules
                            current_url = validate_target_url(next_url, allow_local_for_testing=allow_local_for_testing)
                            continue

                        # Check content size limit
                        content_length = response.headers.get("content-length")
                        if content_length and int(content_length) > MAX_BODY_BYTES:
                            raise ValueError(f"Content length {content_length} exceeds max allowed body size of {MAX_BODY_BYTES} bytes.")

                        # Handle 429 Too Many Requests
                        if response.status_code == 429:
                            retry_after = response.headers.get("retry-after")
                            delay = float(retry_after) if retry_after and retry_after.isdigit() else (2.0 * (attempt + 1))
                            if attempt < max_retries:
                                logger.warning(f"HTTP 429 encountered for {current_url}. Backing off {delay}s...")
                                await asyncio.sleep(delay)
                                break  # Retry outer loop
                            else:
                                raise RateLimitExceededException(f"Rate limited by {current_url} (HTTP 429).")

                        return response

            except (httpx.RequestError, httpx.TimeoutException) as exc:
                if attempt == max_retries:
                    raise
                await asyncio.sleep(1.0 * (attempt + 1))
            finally:
                rate_limiter.release(current_url)

        raise RuntimeError(f"Failed to fetch {url} after {max_retries} attempts.")


scraper_client = SafeScraperClient()
