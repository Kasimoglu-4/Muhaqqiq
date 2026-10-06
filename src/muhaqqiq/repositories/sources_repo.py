"""Sources table access."""

from __future__ import annotations

import sqlite3
from typing import Any

from muhaqqiq import DATA_VERSION


def list_sources(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM sources").fetchall()
    return {"data_version": DATA_VERSION, "sources": [dict(r) for r in rows]}
