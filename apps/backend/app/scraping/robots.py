import time
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse
import urllib.robotparser

import httpx

from app.core.logging import logger
from app.security.ssrf import validate_target_url


class RobotsPolicyEngine:
    """
    Manages per-domain robots.txt retrieval, parsing, and caching.
    Caches parsed rules for 1 hour to minimize unnecessary outbound requests.
    """

    def __init__(self, cache_ttl_seconds: int = 3600):
        self.cache_ttl = cache_ttl_seconds
        # domain -> (parser, fetch_timestamp, crawl_delay)
        self._cache: Dict[str, Tuple[urllib.robotparser.RobotFileParser, float, Optional[float]]] = {}

    def _get_robots_url(self, target_url: str) -> str:
        parsed = urlparse(target_url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    async def get_parser_for_domain(
        self, target_url: str, user_agent: str = "CompanyIntelligenceBot"
    ) -> urllib.robotparser.RobotFileParser:
        parsed = urlparse(target_url)
        domain = parsed.netloc.lower()
        now = time.time()

        if domain in self._cache:
            parser, fetch_time, _ = self._cache[domain]
            if now - fetch_time < self.cache_ttl:
                return parser

        robots_url = self._get_robots_url(target_url)
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)

        try:
            # Validate SSRF on robots.txt target
            safe_robots_url = validate_target_url(robots_url)
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(safe_robots_url, headers={"User-Agent": user_agent})
                if resp.status_code == 200:
                    parser.parse(resp.text.splitlines())
                else:
                    # If 404 or missing, default to allow all
                    parser.parse(["User-agent: *", "Allow: /"])
        except Exception as e:
            logger.warning(f"Could not retrieve robots.txt for {domain}: {str(e)}. Defaulting to permissive.")
            parser.parse(["User-agent: *", "Allow: /"])

        crawl_delay = parser.crawl_delay(user_agent) or parser.crawl_delay("*")
        self._cache[domain] = (parser, now, crawl_delay)
        return parser

    async def is_allowed(self, target_url: str, user_agent: str = "CompanyIntelligenceBot") -> bool:
        """Checks if crawling target_url is permitted by robots.txt."""
        try:
            parser = await self.get_parser_for_domain(target_url, user_agent)
            return parser.can_fetch(user_agent, target_url) or parser.can_fetch("*", target_url)
        except Exception as e:
            logger.error(f"Error checking robots.txt for {target_url}: {str(e)}")
            return True  # Fallback to permissive on error


robots_engine = RobotsPolicyEngine()
