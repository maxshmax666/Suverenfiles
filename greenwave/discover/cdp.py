"""CDP network tap for browser traffic."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from greenwave.models.traffic import NetworkEvent, TrafficKind


class CdpNetworkTap:
    """Capture network events from Chromium through CDP."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[NetworkEvent] = asyncio.Queue()

    async def attach(self, page: Any) -> None:
        """Attach CDP listeners to a Playwright page."""

        session = await page.context.new_cdp_session(page)
        await session.send("Network.enable")
        await session.send("Page.enable")
        await session.send("ServiceWorker.enable")

        session.on("Network.responseReceived", self._on_response_received)
        session.on("Network.webSocketCreated", self._on_websocket_created)

    async def events(self) -> AsyncIterator[NetworkEvent]:
        """Yield captured events until cancelled by the caller."""

        while True:
            yield await self._queue.get()

    def _on_response_received(self, payload: dict[str, Any]) -> None:
        response = payload.get("response", {})
        resource_type = str(payload.get("type", "")).lower()
        kind = self._kind_from_resource(resource_type)
        self._queue.put_nowait(
            NetworkEvent(
                url=str(response.get("url", "")),
                kind=kind,
                method="GET",
                status=response.get("status"),
                response_headers={str(k): str(v) for k, v in response.get("headers", {}).items()},
                resource_type=resource_type,
            )
        )

    def _on_websocket_created(self, payload: dict[str, Any]) -> None:
        self._queue.put_nowait(
            NetworkEvent(
                url=str(payload.get("url", "")),
                kind=TrafficKind.WEBSOCKET,
                resource_type="websocket",
            )
        )

    def _kind_from_resource(self, resource_type: str) -> TrafficKind:
        if resource_type == "xhr":
            return TrafficKind.XHR
        if resource_type == "fetch":
            return TrafficKind.FETCH
        if resource_type == "media":
            return TrafficKind.MEDIA
        if resource_type == "manifest":
            return TrafficKind.MANIFEST
        return TrafficKind.HTTP
