"""Plain substring baseline on norm_skeleton."""

from __future__ import annotations

import sqlite3

from muhaqqiq.normalize import normalize


def baseline_match(conn: sqlite3.Connection, text: str) -> str:
    skeleton = normalize(text)
    if len(skeleton.split()) < 4:
        # still allow exact short hits
        pass
    q = conn.execute(
        "SELECT 1 FROM quran_verses WHERE norm_skeleton LIKE ? LIMIT 1",
        (f"%{skeleton}%",),
    ).fetchone()
    if q:
        return "SUPPORTED"
    h = conn.execute(
        "SELECT 1 FROM hadiths WHERE norm_skeleton LIKE ? LIMIT 1",
        (f"%{skeleton}%",),
    ).fetchone()
    if h:
        return "SUPPORTED"
    c = conn.execute(
        "SELECT 1 FROM known_claims WHERE norm_skeleton LIKE ? LIMIT 1",
        (f"%{skeleton}%",),
    ).fetchone()
    if c:
        return "ATTRIBUTED_RULING"
    return "UNDETERMINED"
