"""GreenWave command-line interface."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from greenwave.config import Settings
from greenwave.database.connection import Database
from greenwave.database.repositories import CameraRepository
from greenwave.discover.engine import DiscoveryEngine
from greenwave.discover.verifier import StreamVerifier
from greenwave.logging import configure_logging
from greenwave.models.stream import StreamDescriptor, StreamType, VerificationResult

app = typer.Typer(no_args_is_help=True, help="GreenWave Recorder CLI.")
console = Console()


@app.callback()
def main() -> None:
    """Configure process-wide logging for CLI commands."""

    configure_logging()


@app.command()
def discover(
    url: Annotated[str, typer.Argument(help="Page URL to discover camera streams from.")],
    db: Annotated[Path, typer.Option(help="SQLite database path.")] = Path("greenwave.sqlite3"),
    output: Annotated[Path, typer.Option(help="cameras.json output path.")] = Path("cameras.json"),
    max_pages: Annotated[int, typer.Option(help="Maximum pages to crawl.")] = 20,
) -> None:
    """Discover streams through real Chromium, verify them, persist them, and export JSON."""

    settings = Settings(database_path=db, output_path=output, max_pages=max_pages)
    result = asyncio.run(DiscoveryEngine(settings).run(url))
    console.print(f"[green]Discovered {len(result.cameras)} camera stream(s).[/green]")


@app.command()
def crawl(url: Annotated[str, typer.Argument(help="Page URL to crawl.")]) -> None:
    """Run crawl diagnostics through the discovery pipeline entrypoint."""

    console.print(f"Use `greenwave discover {url}` for browser-driven crawl and capture.")


@app.command()
def scan(
    url_or_file: Annotated[str, typer.Argument(help="URL or file containing stream URLs.")],
) -> None:
    """Classify and verify direct stream URL(s) without browser traversal."""

    async def _run() -> None:
        targets = _load_scan_targets(url_or_file)
        results = await _verify_scan_targets(targets)
        if len(results) == 1:
            console.print(results[0].model_dump_json(indent=2))
            return
        console.print(f"[green]Verified {len(results)} stream target(s).[/green]")
        for result in results:
            status = "online" if result.online else "offline"
            console.print(f"{status}: {result.stream.type.value} {result.stream.url}")

    asyncio.run(_run())


@app.command("list")
def list_cameras(
    db: Annotated[Path, typer.Option(help="SQLite database path.")] = Path("greenwave.sqlite3"),
) -> None:
    """List stored cameras."""

    async def _run() -> None:
        async with Database(db) as database:
            cameras = await CameraRepository(database).list_cameras()
        table = Table("Name", "Type", "Online", "URL")
        for camera in cameras:
            table.add_row(camera.name, camera.type.value, str(camera.online), str(camera.url))
        console.print(table)

    asyncio.run(_run())


@app.command()
def verify(stream_url: Annotated[str, typer.Argument(help="Direct stream URL to verify.")]) -> None:
    """Verify one direct stream URL."""

    scan(stream_url)


def _guess_direct_type(url: str) -> StreamType:
    lowered = url.lower()
    if ".m3u8" in lowered:
        return StreamType.HLS
    if ".mpd" in lowered:
        return StreamType.DASH
    if lowered.startswith("rtsp://"):
        return StreamType.RTSP
    if lowered.startswith("rtmp://"):
        return StreamType.RTMP
    return StreamType.UNKNOWN_VIDEO


def _load_scan_targets(url_or_file: str) -> list[str]:
    """Return scan targets from a direct URL or a UTF-8 text file.

    File mode intentionally accepts one target per line and ignores empty lines
    and shell-style comments, so operators can keep reusable scan inventories.
    """

    path = Path(url_or_file)
    if not path.exists():
        return [url_or_file]
    if not path.is_file():
        raise typer.BadParameter(f"scan target path is not a file: {path}")

    targets = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not targets:
        raise typer.BadParameter(f"scan target file is empty: {path}")
    return targets


async def _verify_scan_targets(
    targets: Sequence[str],
    *,
    concurrency: int = 10,
) -> list[VerificationResult]:
    """Verify scan targets with bounded concurrency to avoid socket spikes."""

    verifier = StreamVerifier()
    semaphore = asyncio.Semaphore(concurrency)

    async def _verify(target: str) -> VerificationResult:
        async with semaphore:
            descriptor = StreamDescriptor(url=target, type=_guess_direct_type(target))
            return await verifier.verify(descriptor)

    return await asyncio.gather(*(_verify(target) for target in targets))
