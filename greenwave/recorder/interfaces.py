"""Future Recorder phase interfaces."""

from __future__ import annotations

from typing import Protocol

from greenwave.models.stream import StreamDescriptor


class RecorderInterface(Protocol):
    """Contract implemented by future stream recorders."""

    async def record(self, stream: StreamDescriptor, output_dir: str) -> None:
        """Record a stream to the target directory."""
