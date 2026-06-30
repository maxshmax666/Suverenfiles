"""Page action heuristics for click-driven stream discovery."""

from __future__ import annotations

CAMERA_KEYWORDS = ("camera", "cam", "webcam", "video", "stream", "камера", "видео", "трансляция")


def looks_like_camera_label(label: str) -> bool:
    """Return true when a UI label likely represents a camera entry."""

    lowered = label.casefold()
    return any(keyword in lowered for keyword in CAMERA_KEYWORDS)
