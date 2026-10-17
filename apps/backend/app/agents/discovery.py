from typing import Optional
from app.agents.base import BaseAgent
from app.schemas.contracts import DiscoveryResult, ResearchRequest
from app.scraping.crawler import site_crawler


class WebsiteDiscoveryAgent(BaseAgent):
    """
    Agent 2: Website Discovery Agent.
    Discovers relevant company pages, categorizes URL paths, and filters out
    third-party domains.
    """

    def __init__(self):
        super().__init__(name="WebsiteDiscoveryAgent")

    async def execute_task(
        self,
        request: ResearchRequest,
        allow_local_for_testing: bool = False,
    ) -> DiscoveryResult:
        discovery_result, _ = await site_crawler.crawl_site(
            seed_url=request.target_url,
            crawl_depth=request.crawl_depth,
            max_pages=request.max_pages,
            allow_local_for_testing=allow_local_for_testing,
        )
        return discovery_result


discovery_agent = WebsiteDiscoveryAgent()
