"""GreenWave command-line interface."""

from __future__ import annotations

import asyncio
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
from greenwave.models.stream import StreamDescriptor, StreamType

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
    """Classify and verify one direct stream URL without browser traversal."""

    async def _run() -> None:
        descriptor = StreamDescriptor(url=url_or_file, type=_guess_direct_type(url_or_file))
        result = await StreamVerifier().verify(descriptor)
        console.print(result.model_dump_json(indent=2))

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
