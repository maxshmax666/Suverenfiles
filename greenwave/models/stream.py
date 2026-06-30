"""Stream domain models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import AnyUrl, BaseModel, Field, NonNegativeFloat, NonNegativeInt


class StreamType(StrEnum):
    """Supported stream protocol families."""

    HLS = "HLS"
    LL_HLS = "LL_HLS"
    DASH = "DASH"
    RTSP = "RTSP"
    RTMP = "RTMP"
    FLV = "FLV"
    WEBRTC = "WEBRTC"
    MJPEG = "MJPEG"
    MP4_LIVE = "MP4_LIVE"
    UNKNOWN_VIDEO = "UNKNOWN_VIDEO"


class StreamCandidate(BaseModel):
    """Potential video stream extracted from browser traffic."""

    url: str
    method: str = "GET"
    status: int | None = None
    resource_type: str | None = None
    content_type: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    body_sample: str | None = None
    source: str = "network"


class StreamDescriptor(BaseModel):
    """Classified stream with replay context."""

    url: str
    type: StreamType
    headers: dict[str, str] = Field(default_factory=dict)
    cookies: dict[str, str] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class VerificationResult(BaseModel):
    """Result of probing a stream and optional playlist/segments."""

    stream: StreamDescriptor
    online: bool
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    fps: NonNegativeFloat | None = None
    width: NonNegativeInt | None = None
    height: NonNegativeInt | None = None
    codec: str | None = None
    bitrate: NonNegativeInt | None = None
    duration_seconds: NonNegativeFloat | None = None
    playlist_url: str | None = None
    playlist_text: str | None = None
    segments: list[str] = Field(default_factory=list)
    error: str | None = None
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class Camera(BaseModel):
    """Public camera export model."""

    name: str
    url: AnyUrl | str
    type: StreamType
    online: bool
    fps: float | None = None
    width: int | None = None
    height: int | None = None
    codec: str | None = None
    bitrate: int | None = None
