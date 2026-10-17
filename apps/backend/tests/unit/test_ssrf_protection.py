import pytest
from app.core.exceptions import SSRFViolationException
from app.security.ssrf import is_ip_blocked, validate_target_url


def test_is_ip_blocked_private_and_loopback():
    assert is_ip_blocked("127.0.0.1") is True
    assert is_ip_blocked("10.0.0.1") is True
    assert is_ip_blocked("192.168.1.100") is True
    assert is_ip_blocked("172.16.0.1") is True
    assert is_ip_blocked("169.254.169.254") is True
    assert is_ip_blocked("0.0.0.0") is True
    assert is_ip_blocked("::1") is True


def test_is_ip_blocked_public_ips():
    # Public DNS like Google / Cloudflare
    assert is_ip_blocked("8.8.8.8") is False
    assert is_ip_blocked("1.1.1.1") is False


def test_validate_target_url_disallowed_schemes():
    with pytest.raises(SSRFViolationException, match="Only HTTP and HTTPS are permitted"):
        validate_target_url("ftp://example.com")

    with pytest.raises(SSRFViolationException, match="Only HTTP and HTTPS are permitted"):
        validate_target_url("file:///etc/passwd")

    with pytest.raises(SSRFViolationException, match="Only HTTP and HTTPS are permitted"):
        validate_target_url("gopher://example.com")


def test_validate_target_url_blocks_localhost_and_metadata():
    with pytest.raises(SSRFViolationException):
        validate_target_url("http://localhost:8000/internal")

    with pytest.raises(SSRFViolationException):
        validate_target_url("http://127.0.0.1:5432")

    with pytest.raises(SSRFViolationException):
        validate_target_url("http://169.254.169.254/latest/meta-data/")


def test_validate_target_url_allow_local_flag():
    url = validate_target_url("http://localhost:8000", allow_local_for_testing=True)
    assert url == "http://localhost:8000"


def test_validate_target_url_public_domain():
    url = validate_target_url("https://google.com")
    assert url == "https://google.com"
