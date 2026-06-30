"""URL extraction helpers."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse


def same_origin_links(base_url: str, hrefs: list[str]) -> list[str]:
    """Normalize and filter href values to the base URL origin."""

    origin = urlparse(base_url).netloc
    result: list[str] = []
    for href in hrefs:
        absolute = urljoin(base_url, href)
        if urlparse(absolute).netloc == origin:
            result.append(absolute)
    return sorted(set(result))
