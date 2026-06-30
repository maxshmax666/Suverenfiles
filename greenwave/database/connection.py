"""SQLite connection helpers."""

from __future__ import annotations

from pathlib import Path
from types import TracebackType

import aiosqlite

from greenwave.database.schema import SCHEMA_SQL


class Database:
    """Async SQLite database context manager."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.connection: aiosqlite.Connection | None = None

    async def __aenter__(self) -> Database:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = await aiosqlite.connect(self.path)
        self.connection.row_factory = aiosqlite.Row
        await self.connection.executescript(SCHEMA_SQL)
        await self.connection.commit()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.connection is not None:
            await self.connection.close()

    def require_connection(self) -> aiosqlite.Connection:
        """Return the live connection or raise a clear lifecycle error."""

        if self.connection is None:
            raise RuntimeError("Database context has not been entered.")
        return self.connection
