from greenwave.discover.classifier import StreamClassifier
from greenwave.models.stream import StreamCandidate, StreamType


def test_classifies_hls_url() -> None:
    descriptor = StreamClassifier().classify(
        StreamCandidate(url="https://example.test/live/index.m3u8")
    )

    assert descriptor is not None
    assert descriptor.type is StreamType.HLS


def test_classifies_ll_hls_manifest_body() -> None:
    descriptor = StreamClassifier().classify(
        StreamCandidate(
            url="https://example.test/live/index.m3u8",
            body_sample="#EXTM3U\n#EXT-X-PART:DURATION=0.2",
        )
    )

    assert descriptor is not None
    assert descriptor.type is StreamType.LL_HLS


def test_ignores_non_media_url() -> None:
    descriptor = StreamClassifier().classify(StreamCandidate(url="https://example.test/app.js"))

    assert descriptor is None
