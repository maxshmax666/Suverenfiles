from greenwave.cli import app
from typer.testing import CliRunner


def test_cli_help() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "GreenWave Recorder CLI" in result.stdout
