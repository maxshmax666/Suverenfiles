from greenwave.utils.media import parse_hls_manifest


def test_parse_hls_manifest_metadata() -> None:
    manifest = """#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=4500000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2"
variant.m3u8
#EXTINF:4.0,
seg-1.ts
#EXTINF:5.0,
seg-2.ts
"""

    metadata = parse_hls_manifest(manifest, "https://example.test/live/index.m3u8")

    assert metadata.width == 1920
    assert metadata.height == 1080
    assert metadata.bitrate == 4500000
    assert metadata.codec == "avc1.640028,mp4a.40.2"
    assert metadata.duration_seconds == 9.0
    assert metadata.segments == (
        "https://example.test/live/seg-1.ts",
        "https://example.test/live/seg-2.ts",
    )
