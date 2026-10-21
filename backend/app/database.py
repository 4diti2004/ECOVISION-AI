"""SQLite persistence for detection history."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "data/ecovision.db"))


def initialize_database() -> None:
    """Create the local database and detection table."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                waste_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                category TEXT NOT NULL,
                recommended_bin TEXT NOT NULL,
                recommendation_message TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    """Yield a configured database connection."""
    with sqlite3.connect(DATABASE_PATH) as database:
        database.row_factory = sqlite3.Row
        yield database
