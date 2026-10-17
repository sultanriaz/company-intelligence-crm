import html
import re
from typing import Optional
from bs4 import BeautifulSoup


def sanitize_html_to_clean_text(raw_html: str, max_chars: int = 50000) -> str:
    """
    Sanitizes raw HTML by removing scripts, stylesheets, iframes, SVG, and forms,
    and returns normalized readable text with collapsed whitespace.
    """
    if not raw_html:
        return ""

    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove unwanted tags
    for tag in soup(["script", "style", "noscript", "iframe", "svg", "form", "object", "embed", "applet"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # Decode HTML entities
    text = html.unescape(text)

    # Normalize excessive newlines and spaces
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    if len(text) > max_chars:
        text = text[:max_chars] + "\n[Content truncated due to size limits]"

    return text


def sanitize_input_string(value: Optional[str]) -> str:
    """Strips leading/trailing whitespace and control characters from text inputs."""
    if not value:
        return ""
    # Strip null bytes and non-printable control characters except newline and tab
    cleaned = re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]", "", value.strip())
    return cleaned
