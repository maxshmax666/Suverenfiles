"""Playwright browser lifecycle."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import TracebackType
from typing import Any

from greenwave.config import Settings


class BrowserSession:
    """Own Playwright and persistent Chromium context lifecycle."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._playwright: Any | None = None
        self._context: Any | None = None

    async def __aenter__(self) -> BrowserSession:
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:  # pragma: no cover - environment guard
            raise RuntimeError("Playwright is not installed. Run `uv sync` first.") from exc

        self._playwright = await async_playwright().start()
        kwargs: dict[str, object] = {
            "headless": self._settings.browser_headless,
            "user_agent": self._settings.user_agent,
        }
        if self._settings.browser_executable_path is not None:
            kwargs["executable_path"] = str(self._settings.browser_executable_path)
        user_data_dir = Path(self._settings.user_data_dir)
        await asyncio.to_thread(user_data_dir.mkdir, parents=True, exist_ok=True)
        self._context = await self._playwright.chromium.launch_persistent_context(
            str(user_data_dir),
            **kwargs,
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._context is not None:
            await self._context.close()
        if self._playwright is not None:
            await self._playwright.stop()

    async def new_page(self) -> Any:
        """Create a page before navigation so CDP can attach early."""

        if self._context is None:
            raise RuntimeError("BrowserSession must be entered before opening pages.")
        return await self._context.new_page()

    async def goto(self, page: Any, url: str) -> None:
        """Navigate an existing page with production timeouts."""

        await page.goto(
            url,
            wait_until="networkidle",
            timeout=self._settings.timeout_seconds * 1000,
        )

    async def open(self, url: str) -> Any:
        """Open a page in the persistent context."""

        page = await self.new_page()
        await self.goto(page, url)
        return page
