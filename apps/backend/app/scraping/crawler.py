import asyncio
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

from app.core.logging import logger
from app.schemas.contracts import DiscoveredPage, DiscoveryResult, ScrapedPage
from app.scraping.client import scraper_client
from app.scraping.parsers import extract_discovered_links, parse_scraped_page
from app.scraping.robots import robots_engine


class SiteCrawler:
    """
    Crawls authorized websites breadth-first up to configurable depth and page limit.
    Enforces robots.txt compliance, rate limits, and page prioritization.
    """

    def __init__(self, user_agent: str = "CompanyIntelligenceBot"):
        self.user_agent = user_agent
        self.page_cache: Dict[str, ScrapedPage] = {}

    def get_cached_page(self, url: str) -> Optional[ScrapedPage]:
        return self.page_cache.get(url.rstrip("/"))

    async def crawl_site(
        self,
        seed_url: str,
        crawl_depth: int = 2,
        max_pages: int = 15,
        allow_local_for_testing: bool = False,
    ) -> Tuple[DiscoveryResult, List[ScrapedPage]]:
        domain = urlparse(seed_url).netloc.lower()
        visited_urls: Set[str] = set()
        scraped_pages: List[ScrapedPage] = []
        all_discovered: Dict[str, DiscoveredPage] = {}

        # Queue: list of (url, current_depth)
        queue: List[Tuple[str, int]] = [(seed_url, 0)]
        all_discovered[seed_url] = DiscoveredPage(url=seed_url, category="home", priority=1)

        while queue and len(scraped_pages) < max_pages:
            current_url, depth = queue.pop(0)

            # Skip if already visited
            normalized_current = current_url.rstrip("/")
            if normalized_current in visited_urls:
                continue

            # Check robots.txt
            if not allow_local_for_testing:
                is_allowed = await robots_engine.is_allowed(current_url, self.user_agent)
                if not is_allowed:
                    logger.info(f"Skipping {current_url} per robots.txt policy.")
                    continue

            visited_urls.add(normalized_current)

            try:
                response = await scraper_client.fetch_page(current_url, allow_local_for_testing=allow_local_for_testing)
                if response.status_code == 200:
                    html = response.text
                    page = parse_scraped_page(current_url, html, status_code=response.status_code)
                    scraped_pages.append(page)

                    # Discover links if depth permits
                    if depth < crawl_depth:
                        new_links = extract_discovered_links(current_url, html)
                        # Sort by priority (1 is highest)
                        new_links.sort(key=lambda x: x.priority)

                        for link in new_links:
                            norm_link = link.url.rstrip("/")
                            if norm_link not in all_discovered:
                                all_discovered[norm_link] = link
                                if norm_link not in visited_urls:
                                    queue.append((link.url, depth + 1))

            except Exception as e:
                logger.warning(f"Error scraping {current_url}: {str(e)}")

        discovery_result = DiscoveryResult(
            domain=domain,
            seed_url=seed_url,
            total_discovered=len(all_discovered),
            pages=list(all_discovered.values()),
            discovery_metadata={
                "pages_scraped": str(len(scraped_pages)),
                "crawl_depth_applied": str(crawl_depth),
            },
        )

        for p in scraped_pages:
            self.page_cache[p.url.rstrip("/")] = p

        return discovery_result, scraped_pages


site_crawler = SiteCrawler()
