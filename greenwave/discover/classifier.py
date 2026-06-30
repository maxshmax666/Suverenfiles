"""Stream classification rules."""

from __future__ import annotations

from urllib.parse import urlparse

from greenwave.models.stream import StreamCandidate, StreamDescriptor, StreamType


class StreamClassifier:
    """Classify network observations into stream descriptors."""

    def classify(self, candidate: StreamCandidate) -> StreamDescriptor | None:
        """Return a stream descriptor if the candidate looks like video traffic."""

        stream_type = self.detect_type(candidate)
        if stream_type is None:
            return None
        return StreamDescriptor(
            url=candidate.url,
            type=stream_type,
            headers=candidate.headers,
            confidence=self._confidence(candidate, stream_type),
        )

    def detect_type(self, candidate: StreamCandidate) -> StreamType | None:
        """Detect the stream family from URL, headers, resource type, and body sample."""

        url = candidate.url.lower()
        parsed = urlparse(url)
        content_type = (candidate.content_type or "").lower()
        body = (candidate.body_sample or "").lstrip().lower()

        if parsed.scheme == "rtsp":
            return StreamType.RTSP
        if parsed.scheme == "rtmp":
            return StreamType.RTMP
        if ".m3u8" in url or "application/vnd.apple.mpegurl" in content_type:
            if "#ext-x-part" in body or "_hls" in url and "part" in url:
                return StreamType.LL_HLS
            return StreamType.HLS
        if ".mpd" in url or "dash+xml" in content_type or body.startswith("<mpd"):
            return StreamType.DASH
        if ".flv" in url or "video/x-flv" in content_type:
            return StreamType.FLV
        if "multipart/x-mixed-replace" in content_type or "mjpeg" in url:
            return StreamType.MJPEG
        if "webrtc" in url or "application/sdp" in content_type or "a=ice" in body:
            return StreamType.WEBRTC
        if ".mp4" in url or content_type in {"video/mp4", "application/mp4"}:
            return StreamType.MP4_LIVE
        if candidate.resource_type == "media" or content_type.startswith("video/"):
            return StreamType.UNKNOWN_VIDEO
        return None

    def _confidence(self, candidate: StreamCandidate, stream_type: StreamType) -> float:
        if stream_type in {StreamType.HLS, StreamType.LL_HLS, StreamType.DASH}:
            return 0.95
        if candidate.content_type and candidate.content_type.startswith(("video/", "application/")):
            return 0.8
        return 0.65
