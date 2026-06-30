from pathlib import Path

from greenwave.cli import app
from greenwave.cli import _load_scan_targets
from typer.testing import CliRunner


def test_cli_help() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "GreenWave Recorder CLI" in result.stdout


def test_load_scan_targets_from_direct_url() -> None:
    assert _load_scan_targets("https://example.test/live/index.m3u8") == [
        "https://example.test/live/index.m3u8"
    ]


def test_load_scan_targets_from_file(tmp_path: Path) -> None:
    scan_file = tmp_path / "streams.txt"
    scan_file.write_text(
        """
# primary camera
https://example.test/live/index.m3u8

rtsp://camera.example.test/live
""",
        encoding="utf-8",
    )

    assert _load_scan_targets(str(scan_file)) == [
        "https://example.test/live/index.m3u8",
        "rtsp://camera.example.test/live",
    ]
