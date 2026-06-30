"""Future Analyzer phase interfaces."""

from __future__ import annotations

from typing import Protocol


class AnalyzerInterface(Protocol):
    """Contract implemented by future video analyzers."""

    async def analyze(self, media_path: str) -> dict[str, object]:
        """Analyze a recorded media file and return structured findings."""
