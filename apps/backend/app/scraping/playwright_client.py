from typing import Optional
from app.core.config import settings
from app.core.logging import logger
from app.scraping.client import scraper_client
from app.security.ssrf import validate_target_url


class PlaywrightDynamicRenderer:
    """
    Renders JavaScript-heavy Single Page Applications using Playwright.
    Provides graceful fallback to static SafeScraperClient if Playwright is disabled or unavailable.
    """

    def __init__(self, is_enabled: bool = False):
        self.enabled = is_enabled

    async def render_page_html(
        self,
        url: str,
        allow_local_for_testing: bool = False,
    ) -> str:
        safe_url = validate_target_url(url, allow_local_for_testing=allow_local_for_testing)

        if not self.enabled:
            # Fallback to static HTTPX client
            response = await scraper_client.fetch_page(safe_url, allow_local_for_testing=allow_local_for_testing)
            return response.text

        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(user_agent=settings.SCRAPER_USER_AGENT)
                await page.goto(safe_url, timeout=settings.SCRAPER_TIMEOUT_SECONDS * 1000, wait_until="networkidle")
                content = await page.content()
                await browser.close()
                return content
        except Exception as e:
            logger.warning(f"Playwright rendering failed for {safe_url}: {str(e)}. Falling back to static HTTPX.")
            response = await scraper_client.fetch_page(safe_url, allow_local_for_testing=allow_local_for_testing)
            return response.text


playwright_renderer = PlaywrightDynamicRenderer(is_enabled=settings.PLAYWRIGHT_ENABLED)
