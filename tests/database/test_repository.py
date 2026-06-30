from pathlib import Path

import pytest
from greenwave.database.connection import Database
from greenwave.database.repositories import CameraRepository
from greenwave.models.stream import StreamDescriptor, StreamType, VerificationResult


@pytest.mark.asyncio
async def test_repository_persists_verification(tmp_path: Path) -> None:
    db_path = tmp_path / "greenwave.sqlite3"
    stream = StreamDescriptor(url="https://example.test/live/index.m3u8", type=StreamType.HLS)
    result = VerificationResult(
        stream=stream,
        online=True,
        width=1280,
        height=720,
        codec="avc1",
        bitrate=2_000_000,
        playlist_url=stream.url,
        playlist_text="#EXTM3U\n#EXT-X-ENDLIST\n",
        segments=["https://example.test/live/seg.ts"],
        raw_metadata={"content_type": "application/vnd.apple.mpegurl", "is_live": False},
    )

    async with Database(db_path) as database:
        repository = CameraRepository(database)
        await repository.save_verifications("https://example.test/cameras", [result])
        cameras = await repository.list_cameras()

    assert len(cameras) == 1
    assert cameras[0].name == "index"
    assert cameras[0].online is True
    assert cameras[0].width == 1280
