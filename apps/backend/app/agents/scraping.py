from typing import List
from app.agents.base import BaseAgent
from app.schemas.contracts import DiscoveryResult, ScrapedPage
from app.scraping.client import scraper_client
from app.scraping.crawler import site_crawler
from app.scraping.parsers import parse_scraped_page
from app.scraping.playwright_client import playwright_renderer


class WebScrapingAgent(BaseAgent):
    """
    Agent 3: Web Scraping Agent.
    Retrieves permitted pages, parses HTML content, normalizes text,
    and extracts contact channels and content hashes.
    """

    def __init__(self):
        super().__init__(name="WebScrapingAgent")

    async def execute_task(
        self,
        discovery_result: DiscoveryResult,
        allow_local_for_testing: bool = False,
    ) -> List[ScrapedPage]:
        scraped_pages: List[ScrapedPage] = []

        # Sort pages by priority and limit to top 8 priority pages (home, about, contact, products)
        pages_to_scrape = sorted(discovery_result.pages, key=lambda p: p.priority)[:8]

        for page_info in pages_to_scrape:
            # Check if page was already fetched and parsed during discovery
            cached = site_crawler.get_cached_page(page_info.url)
            if cached:
                scraped_pages.append(cached)
                continue

            try:
                # Use dynamic renderer (with static HTTPX fallback)
                html_text = await playwright_renderer.render_page_html(
                    page_info.url,
                    allow_local_for_testing=allow_local_for_testing,
                )
                if html_text:
                    parsed = parse_scraped_page(page_info.url, html_text, status_code=200)
                    scraped_pages.append(parsed)
            except Exception as e:
                # Non-fatal for individual secondary page
                pass

        return scraped_pages


scraping_agent = WebScrapingAgent()
