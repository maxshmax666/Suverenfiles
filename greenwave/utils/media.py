"""Media manifest parsing helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

_RESOLUTION_RE = re.compile(r"RESOLUTION=(?P<width>\d+)x(?P<height>\d+)")
_BANDWIDTH_RE = re.compile(r"(?:AVERAGE-)?BANDWIDTH=(?P<bitrate>\d+)")
_CODECS_RE = re.compile(r'CODECS="(?P<codec>[^"]+)"')
_DURATION_RE = re.compile(r"#EXTINF:(?P<duration>[0-9.]+)")


@dataclass(frozen=True, slots=True)
class ManifestMetadata:
    """Best-effort metadata extracted from a media manifest."""

    width: int | None = None
    height: int | None = None
    codec: str | None = None
    bitrate: int | None = None
    duration_seconds: float | None = None
    fps: float | None = None
    segments: tuple[str, ...] = ()
    is_live: bool = True


def parse_hls_manifest(text: str, base_url: str) -> ManifestMetadata:
    """Parse common HLS and Low Latency HLS metadata without downloading media bytes."""

    width: int | None = None
    height: int | None = None
    bitrate: int | None = None
    codec: str | None = None
    durations: list[float] = []
    segments: list[str] = []

    for line in (line.strip() for line in text.splitlines()):
        if not line:
            continue
        if match := _RESOLUTION_RE.search(line):
            width = int(match.group("width"))
            height = int(match.group("height"))
        if match := _BANDWIDTH_RE.search(line):
            bitrate = int(match.group("bitrate"))
        if match := _CODECS_RE.search(line):
            codec = match.group("codec")
        if match := _DURATION_RE.search(line):
            durations.append(float(match.group("duration")))
        if not line.startswith("#") and _looks_like_segment(line):
            segments.append(urljoin(base_url, line))

    total_duration = sum(durations) if durations else None
    return ManifestMetadata(
        width=width,
        height=height,
        codec=codec,
        bitrate=bitrate,
        duration_seconds=total_duration,
        segments=tuple(segments),
        is_live="#EXT-X-ENDLIST" not in text,
    )


def _looks_like_segment(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in (".ts", ".m4s", ".mp4", ".aac", ".cmfv", ".cmfa"))
