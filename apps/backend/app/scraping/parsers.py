import hashlib
import re
from typing import Dict, List, Set, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from app.schemas.contracts import DiscoveredPage, ScrapedPage
from app.security.sanitization import sanitize_html_to_clean_text

# Regex patterns for business intelligence discovery
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}")

# Domain extensions/junk to ignore in email extraction
INVALID_EMAIL_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js"}

CATEGORY_KEYWORDS = {
    "about": ["about", "about-us", "company", "who-we-are", "story", "team", "mission", "leadership"],
    "services": ["services", "solutions", "capabilities", "what-we-do", "consulting"],
    "products": ["products", "platform", "features", "software", "product", "demo"],
    "careers": ["careers", "jobs", "join-us", "work-with-us", "hiring"],
    "contact": ["contact", "contact-us", "get-in-touch", "reach-us", "location"],
    "pricing": ["pricing", "plans", "cost"],
    "news": ["news", "blog", "press", "media", "articles", "insights"],
}


def categorize_url_path(url: str) -> Tuple[str, int]:
    """
    Categorizes a URL path and assigns crawl priority.
    Returns (category, priority 1-5).
    """
    path = urlparse(url).path.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in path:
                if cat in {"about", "products", "services"}:
                    return cat, 1  # Highest priority
                elif cat in {"contact", "careers"}:
                    return cat, 2
                else:
                    return cat, 3
    return "general", 4


def extract_discovered_links(base_url: str, html_content: str) -> List[DiscoveredPage]:
    """
    Extracts, normalizes, deduplicates, and categorizes internal links within the same domain.
    """
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, "html.parser")
    base_domain = urlparse(base_url).netloc.lower()
    discovered: Dict[str, DiscoveredPage] = {}

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("tel:"):
            continue

        absolute_url = urljoin(base_url, href)
        parsed = urlparse(absolute_url)

        # Ignore non-http/https
        if parsed.scheme.lower() not in {"http", "https"}:
            continue

        # Strictly enforce internal domain scope (subdomains allowed or exact root)
        link_domain = parsed.netloc.lower()
        if link_domain != base_domain and not link_domain.endswith("." + base_domain):
            continue

        # Normalize URL: strip fragment and trailing slash
        normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
        if parsed.query:
            normalized_url += f"?{parsed.query}"

        # Skip file downloads
        lower_path = parsed.path.lower()
        if any(lower_path.endswith(ext) for ext in [".pdf", ".zip", ".exe", ".dmg", ".tar", ".gz"]):
            continue

        if normalized_url not in discovered:
            category, priority = categorize_url_path(normalized_url)
            link_text = a_tag.get_text(strip=True)[:100]
            discovered[normalized_url] = DiscoveredPage(
                url=normalized_url,
                category=category,
                priority=priority,
                title=link_text or None,
            )

    return list(discovered.values())


def extract_emails(html_content: str) -> List[str]:
    """Extracts valid unique email addresses from HTML text and mailto: tags."""
    emails: Set[str] = set()

    # mailto tags
    soup = BeautifulSoup(html_content, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().startswith("mailto:"):
            raw_email = href[7:].split("?")[0].strip().lower()
            if EMAIL_REGEX.match(raw_email):
                emails.add(raw_email)

    # General regex search
    matches = EMAIL_REGEX.findall(html_content)
    for email in matches:
        email_clean = email.strip().lower()
        # Filter out junk extensions
        if not any(email_clean.endswith(ext) for ext in INVALID_EMAIL_EXTENSIONS):
            if not email_clean.startswith("user@") and not email_clean.endswith("example.com"):
                emails.add(email_clean)

    return sorted(list(emails))


def extract_social_links(soup: BeautifulSoup) -> Dict[str, str]:
    """Extracts official social channel links."""
    socials: Dict[str, str] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        lower_href = href.lower()
        if "linkedin.com/company" in lower_href or "linkedin.com/in" in lower_href:
            socials["linkedin"] = href
        elif "twitter.com/" in lower_href or "x.com/" in lower_href:
            socials["twitter"] = href
        elif "github.com/" in lower_href:
            socials["github"] = href
        elif "facebook.com/" in lower_href:
            socials["facebook"] = href
        elif "youtube.com/" in lower_href:
            socials["youtube"] = href
    return socials


def parse_scraped_page(url: str, html_content: str, status_code: int = 200, is_js: bool = False) -> ScrapedPage:
    """Parses raw HTML into a structured ScrapedPage model."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # Meta Description
    meta_desc = ""
    desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)}) or soup.find(
        "meta", attrs={"property": "og:description"}
    )
    if desc_tag and desc_tag.get("content"):
        meta_desc = desc_tag["content"].strip()

    # Normalized clean text
    clean_text = sanitize_html_to_clean_text(html_content)

    # Content SHA256 hash
    content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

    # Emails & Socials
    emails = extract_emails(html_content)
    social_links = extract_social_links(soup)

    return ScrapedPage(
        url=url,
        http_status=status_code,
        title=title,
        meta_description=meta_desc,
        clean_text=clean_text,
        content_hash=content_hash,
        discovered_emails=emails,
        discovered_phones=[],
        social_links=social_links,
        is_rendered_js=is_js,
    )
