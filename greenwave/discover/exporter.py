"""JSON export support."""

from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

from greenwave.models.stream import Camera


class JsonExporter:
    """Write deterministic camera exports atomically."""

    async def export_cameras(self, cameras: list[Camera], path: Path) -> None:
        """Export cameras to UTF-8 JSON using atomic replace semantics."""

        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        payload = [
            camera.model_dump(mode="json") for camera in sorted(cameras, key=lambda item: item.name)
        ]
        encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(encoded)
        await asyncio.to_thread(temp_path.replace, path)
