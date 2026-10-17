import ipaddress
import socket
from urllib.parse import urlparse
from typing import List, Tuple

from app.core.exceptions import SSRFViolationException

# Disallowed IP ranges (Private, Loopback, Link-Local, Cloud Metadata, Multicast, Reserved)
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),       # Includes AWS/GCP/Azure metadata 169.254.169.254
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.88.99.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6 blocked ranges
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("::ffff:0:0/96"),
]

ALLOWED_SCHEMES = {"http", "https"}


def is_ip_blocked(ip_str: str) -> bool:
    """Checks if an IP address string falls inside any blocked subnet."""
    try:
        ip = ipaddress.ip_address(ip_str)
        # Check standard properties
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return True

        for network in BLOCKED_IP_NETWORKS:
            if ip in network:
                return True
        return False
    except ValueError:
        return True


def resolve_hostname_ips(hostname: str) -> List[str]:
    """Resolves hostname to IPv4 and IPv6 addresses using getaddrinfo."""
    try:
        addr_info = socket.getaddrinfo(hostname, None)
        ips = list({info[4][0] for info in addr_info if info[4]})
        return ips
    except socket.gaierror as e:
        raise SSRFViolationException(f"Failed to resolve hostname '{hostname}': {str(e)}")


def validate_target_url(url: str, allow_local_for_testing: bool = False) -> str:
    """
    Validates a URL against SSRF vulnerabilities:
    - Protocol scheme must be http or https
    - Hostname must be present and resolve to public routable IP addresses
    """
    if not url or not isinstance(url, str):
        raise SSRFViolationException("URL must be a non-empty string.")

    url = url.strip()
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise SSRFViolationException(f"Invalid URL scheme '{parsed.scheme}'. Only HTTP and HTTPS are permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFViolationException("URL has no valid hostname.")

    # Block obvious local names
    lower_host = hostname.lower()
    if lower_host in {"localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"}:
        if not allow_local_for_testing:
            raise SSRFViolationException(f"Access to local or metadata host '{hostname}' is blocked.")

    # Directly check if hostname is already an IP address
    try:
        ip_obj = ipaddress.ip_address(hostname)
        if not allow_local_for_testing and is_ip_blocked(str(ip_obj)):
            raise SSRFViolationException(f"Target IP address '{hostname}' is blocked by SSRF policy.")
        return url
    except ValueError:
        pass  # Hostname is a domain name, proceed to DNS resolution

    if not allow_local_for_testing:
        resolved_ips = resolve_hostname_ips(hostname)
        if not resolved_ips:
            raise SSRFViolationException(f"No IP addresses resolved for '{hostname}'.")

        for ip in resolved_ips:
            if is_ip_blocked(ip):
                raise SSRFViolationException(
                    f"Hostname '{hostname}' resolved to prohibited IP address '{ip}' (SSRF defense)."
                )

    return url
