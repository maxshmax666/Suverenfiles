"""Conservative browser crawler primitives."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse


@dataclass(frozen=True, slots=True)
class CrawlAction:
    """A browser action executed or proposed by the crawler."""

    url: str
    action: str
    label: str | None = None


class SiteCrawler:
    """Discover same-site links and clickable camera-like UI elements."""

    def __init__(self, max_pages: int = 20) -> None:
        self._max_pages = max_pages

    async def crawl(self, page: Any) -> AsyncIterator[CrawlAction]:
        """Yield same-origin navigation actions from a Playwright page."""

        current_url = page.url
        origin = urlparse(current_url).netloc
        script = (
            "elements => elements.map(a => "
            "({href: a.href, text: a.innerText || a.ariaLabel || ''}))"
        )
        anchors = await page.locator("a[href]").evaluate_all(script)
        yielded = 0
        for anchor in anchors:
            href = str(anchor.get("href") or "")
            if not href:
                continue
            absolute = urljoin(current_url, href)
            if urlparse(absolute).netloc != origin:
                continue
            yield CrawlAction(
                url=absolute, action="open_link", label=str(anchor.get("text") or "")[:120]
            )
            yielded += 1
            if yielded >= self._max_pages:
                return
