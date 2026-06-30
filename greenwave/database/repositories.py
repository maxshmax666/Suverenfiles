"""SQLite repositories."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from greenwave.database.connection import Database
from greenwave.models.stream import Camera, VerificationResult


class CameraRepository:
    """Persist and query discovered cameras and streams."""

    def __init__(self, database: Database) -> None:
        self._database = database

    async def save_verifications(self, site_url: str, results: list[VerificationResult]) -> None:
        """Persist verification results using idempotent upserts."""

        connection = self._database.require_connection()
        site_id = await self._upsert_site(site_url)
        for index, result in enumerate(results, start=1):
            camera_name = _camera_name_from_url(result.stream.url, index)
            camera_id = await self._upsert_camera(
                site_id=site_id,
                name=camera_name,
                page_url=site_url,
                status="online" if result.online else "offline",
            )
            stream_id = await self._upsert_stream(camera_id, result)
            if result.playlist_url and result.playlist_text is not None:
                await self._insert_playlist(stream_id, result)
        await connection.commit()

    async def list_cameras(self) -> list[Camera]:
        """Return exported cameras from stored stream rows."""

        connection = self._database.require_connection()
        cursor = await connection.execute(
            """
            SELECT cameras.name, streams.url, streams.type, streams.online, streams.fps,
                   streams.width, streams.height, streams.codec, streams.bitrate
            FROM cameras
            JOIN streams ON streams.camera_id = cameras.id
            ORDER BY cameras.name, streams.url
            """
        )
        rows = await cursor.fetchall()
        return [
            Camera(
                name=str(row["name"]),
                url=str(row["url"]),
                type=row["type"],
                online=bool(row["online"]),
                fps=row["fps"],
                width=row["width"],
                height=row["height"],
                codec=row["codec"],
                bitrate=row["bitrate"],
            )
            for row in rows
        ]

    async def _upsert_site(self, url: str) -> int:
        connection = self._database.require_connection()
        await connection.execute(
            """
            INSERT INTO sites(url) VALUES (?)
            ON CONFLICT(url) DO UPDATE SET last_seen_at = CURRENT_TIMESTAMP
            """,
            (url,),
        )
        cursor = await connection.execute("SELECT id FROM sites WHERE url = ?", (url,))
        row = await cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to upsert site.")
        return int(row["id"])

    async def _upsert_camera(self, site_id: int, name: str, page_url: str, status: str) -> int:
        connection = self._database.require_connection()
        await connection.execute(
            """
            INSERT INTO cameras(site_id, name, page_url, status) VALUES (?, ?, ?, ?)
            ON CONFLICT(site_id, name, page_url) DO UPDATE SET
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
            """,
            (site_id, name, page_url, status),
        )
        cursor = await connection.execute(
            "SELECT id FROM cameras WHERE site_id = ? AND name = ? AND page_url = ?",
            (site_id, name, page_url),
        )
        row = await cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to upsert camera.")
        return int(row["id"])

    async def _upsert_stream(self, camera_id: int, result: VerificationResult) -> int:
        connection = self._database.require_connection()
        await connection.execute(
            """
            INSERT INTO streams(
                camera_id, url, type, online, fps, width, height, codec, bitrate,
                duration_seconds, headers_json, cookies_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(camera_id, url) DO UPDATE SET
                type = excluded.type,
                online = excluded.online,
                fps = excluded.fps,
                width = excluded.width,
                height = excluded.height,
                codec = excluded.codec,
                bitrate = excluded.bitrate,
                duration_seconds = excluded.duration_seconds,
                headers_json = excluded.headers_json,
                cookies_json = excluded.cookies_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                camera_id,
                result.stream.url,
                result.stream.type.value,
                int(result.online),
                result.fps,
                result.width,
                result.height,
                result.codec,
                result.bitrate,
                result.duration_seconds,
                json.dumps(result.stream.headers, sort_keys=True),
                json.dumps(result.stream.cookies, sort_keys=True),
            ),
        )
        cursor = await connection.execute(
            "SELECT id FROM streams WHERE camera_id = ? AND url = ?",
            (camera_id, result.stream.url),
        )
        row = await cursor.fetchone()
        if row is None:
            raise RuntimeError("Failed to upsert stream.")
        return int(row["id"])

    async def _insert_playlist(self, stream_id: int, result: VerificationResult) -> None:
        connection = self._database.require_connection()
        text = result.playlist_text or ""
        await connection.execute(
            """
            INSERT INTO playlists(stream_id, url, content_type, body_sha256, is_live, raw_text)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                stream_id,
                result.playlist_url,
                result.raw_metadata.get("content_type"),
                hashlib.sha256(text.encode("utf-8")).hexdigest(),
                int(bool(result.raw_metadata.get("is_live", True))),
                text[:200_000],
            ),
        )


def _camera_name_from_url(url: str, index: int) -> str:
    stem = Path(url.split("?", 1)[0]).stem
    return stem.lower().replace("-", "_") or f"camera_{index}"
