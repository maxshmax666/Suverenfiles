"""Typed network event models used by the discovery pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TrafficKind(StrEnum):
    """Network event families collected from Playwright and CDP."""

    HTTP = "HTTP"
    FETCH = "FETCH"
    XHR = "XHR"
    WEBSOCKET = "WEBSOCKET"
    MEDIA = "MEDIA"
    MANIFEST = "MANIFEST"
    SERVICE_WORKER = "SERVICE_WORKER"


class NetworkEvent(BaseModel):
    """Normalized network observation."""

    url: str
    kind: TrafficKind
    method: str = "GET"
    status: int | None = None
    request_headers: dict[str, str] = Field(default_factory=dict)
    response_headers: dict[str, str] = Field(default_factory=dict)
    body_sample: str | None = None
    resource_type: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
