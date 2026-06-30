"""Future Web UI and REST API interfaces."""

from __future__ import annotations

from typing import Protocol

from greenwave.models.stream import Camera


class WebInterface(Protocol):
    """Contract implemented by future API/UI adapters."""

    async def list_cameras(self) -> list[Camera]:
        """Return cameras visible to API clients."""
