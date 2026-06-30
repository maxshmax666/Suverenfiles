"""Discovery orchestration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import structlog

from greenwave.config import Settings
from greenwave.database.connection import Database
from greenwave.database.repositories import CameraRepository
from greenwave.discover.browser import BrowserSession
from greenwave.discover.cdp import CdpNetworkTap
from greenwave.discover.classifier import StreamClassifier
from greenwave.discover.exporter import JsonExporter
from greenwave.discover.traffic import TrafficCollector
from greenwave.discover.verifier import StreamVerifier
from greenwave.models.stream import Camera, VerificationResult

_LOG = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    """High-level result returned by the discover command."""

    cameras: list[Camera]
    verifications: list[VerificationResult]


class DiscoveryEngine:
    """Coordinate browser discovery, classification, verification, persistence, and export."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._classifier = StreamClassifier()
        self._verifier = StreamVerifier(timeout_seconds=settings.timeout_seconds)
        self._exporter = JsonExporter()

    async def run(self, target_url: str) -> DiscoveryResult:
        """Run browser-driven discovery for one target URL."""

        collector = TrafficCollector()
        async with BrowserSession(self._settings) as browser:
            page = await browser.new_page()
            tap = CdpNetworkTap()
            await tap.attach(page)
            await browser.goto(page, target_url)
            await asyncio.sleep(2)
            await self._drain_events(tap, collector)

        descriptors = [
            descriptor
            for candidate in collector.candidates()
            if (descriptor := self._classifier.classify(candidate)) is not None
        ]
        unique_descriptors = {descriptor.url: descriptor for descriptor in descriptors}.values()
        verifications = await asyncio.gather(
            *(self._verifier.verify(descriptor) for descriptor in unique_descriptors)
        )
        async with Database(self._settings.database_path) as database:
            repository = CameraRepository(database)
            await repository.save_verifications(target_url, verifications)
            cameras = await repository.list_cameras()
        await self._exporter.export_cameras(cameras, self._settings.output_path)
        _LOG.info("discovery_finished", cameras=len(cameras), streams=len(verifications))
        return DiscoveryResult(cameras=cameras, verifications=list(verifications))

    async def _drain_events(self, tap: CdpNetworkTap, collector: TrafficCollector) -> None:
        """Drain queued CDP events without blocking the discovery flow forever."""

        event_iterator = tap.events().__aiter__()
        while True:
            try:
                event = await asyncio.wait_for(event_iterator.__anext__(), timeout=0.1)
            except TimeoutError:
                break
            collector.record(event)
