"""Local URL-shape checks. Reputation providers can be added behind this boundary."""

import ipaddress
import re
from urllib.parse import urlsplit

from .schemas import EvidenceSignal


SHORTENERS = {
    "bit.ly", "cutt.ly", "is.gd", "rb.gy", "shorturl.at", "tiny.cc", "tinyurl.com", "t.co"
}
HOSTED_PLATFORMS = ("vercel.app", "netlify.app", "pages.dev", "github.io")
BRAND_TERMS = ("bank", "ecobank", "fidelity", "gcb", "momo", "mtn", "telecel")


def _signal(key: str, label: str, weight: int, evidence: str) -> EvidenceSignal:
    return EvidenceSignal(key, label, weight, 1.0, "url", evidence)


def extract_hostname(content: str) -> str:
    candidate = content.strip()
    if not re.match(r"^[a-z][a-z0-9+.-]*://", candidate, re.I):
        candidate = f"https://{candidate}"
    parsed = urlsplit(candidate)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if not hostname or " " in hostname or ("." not in hostname and hostname != "localhost"):
        raise ValueError("Enter a valid URL or domain name")
    return hostname


def analyse_url(content: str) -> list[EvidenceSignal]:
    candidate = content.strip()
    if not re.match(r"^[a-z][a-z0-9+.-]*://", candidate, re.I):
        candidate = f"https://{candidate}"
    parsed = urlsplit(candidate)
    hostname = extract_hostname(content)

    signals: list[EvidenceSignal] = []
    if parsed.scheme.lower() != "https":
        signals.append(_signal("insecure_url", "Does not use an encrypted HTTPS connection", 8, "The URL uses HTTP rather than HTTPS."))
    try:
        ipaddress.ip_address(hostname.strip("[]"))
        signals.append(_signal("ip_address_url", "Uses an IP address instead of a recognizable domain", 22, "Direct IP links hide the expected organization domain."))
    except ValueError:
        pass
    if hostname.startswith("xn--") or ".xn--" in hostname:
        signals.append(_signal("punycode_domain", "Uses an internationalized domain encoding", 18, "Punycode can be legitimate but is also used for look-alike domains."))
    if hostname in SHORTENERS:
        signals.append(_signal("shortened_url", "Uses a shortened link that hides its destination", 20, "Expand and verify shortened links before opening them."))
    if "@" in parsed.netloc:
        signals.append(_signal("url_credentials", "Contains misleading account information in the URL", 25, "Text before @ can disguise the real destination host."))
    hosted = next((suffix for suffix in HOSTED_PLATFORMS if hostname == suffix or hostname.endswith(f".{suffix}")), None)
    brand_context = f"{hostname}{parsed.path}".lower()
    if hosted and any(term in brand_context for term in BRAND_TERMS):
        signals.append(_signal("suspicious_domain", "Uses a brand-like name on a general hosting domain", 28, "The named organization does not control the underlying hosting domain."))
    return signals
