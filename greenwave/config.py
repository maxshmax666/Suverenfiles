"""Application configuration."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated GreenWave runtime settings."""

    model_config = SettingsConfigDict(env_prefix="GREENWAVE_", env_file=".env", extra="ignore")

    database_path: Path = Path("greenwave.sqlite3")
    output_path: Path = Path("cameras.json")
    browser_headless: bool = True
    browser_executable_path: Path | None = None
    user_data_dir: Path = Path(".greenwave-browser")
    timeout_seconds: PositiveInt = 30
    max_pages: PositiveInt = 20
    max_clicks_per_page: PositiveInt = 50
    max_concurrency: PositiveInt = 6
    user_agent: str = Field(
        default=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
    )
