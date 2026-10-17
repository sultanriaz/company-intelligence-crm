import os
from app.scraping.parsers import extract_discovered_links, extract_emails, parse_scraped_page


def get_sample_html() -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_site.html")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_extract_emails_from_html():
    html = get_sample_html()
    emails = extract_emails(html)
    assert "contact@acme.example.com" in emails


def test_extract_discovered_links():
    html = get_sample_html()
    links = extract_discovered_links("https://acme.example.com", html)
    urls = [l.url for l in links]

    assert "https://acme.example.com/about" in urls
    assert "https://acme.example.com/services" in urls
    assert "https://acme.example.com/products" in urls
    assert "https://acme.example.com/contact" in urls

    about_link = next(l for l in links if "about" in l.url)
    assert about_link.category == "about"
    assert about_link.priority == 1


def test_parse_scraped_page():
    html = get_sample_html()
    page = parse_scraped_page("https://acme.example.com", html, status_code=200)

    assert "Acme Innovations" in page.title
    assert "automated ETL pipelines" in page.meta_description
    assert len(page.clean_text) > 0
    assert len(page.content_hash) == 64
    assert "contact@acme.example.com" in page.discovered_emails
    assert "linkedin" in page.social_links
