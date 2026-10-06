"""Card persistence — stores hash + status + diffs, never raw user text."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any

from muhaqqiq import DATA_VERSION


def input_hash(norm_skeleton: str) -> str:
    return hashlib.sha256(f"{norm_skeleton}|{DATA_VERSION}".encode()).hexdigest()


def card_id(norm_skeleton: str) -> str:
    return input_hash(norm_skeleton)[:12]


def upsert_card(
    conn: sqlite3.Connection,
    *,
    status: str,
    norm_skeleton: str,
    match_refs: list[dict[str, Any]],
    score: float | None,
    diff: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> str:
    cid = card_id(norm_skeleton)
    ih = input_hash(norm_skeleton)
    conn.execute(
        """
        INSERT INTO cards (id, input_hash, status, match_refs, score, diff_json, extras_json, data_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          status=excluded.status,
          match_refs=excluded.match_refs,
          score=excluded.score,
          diff_json=excluded.diff_json,
          extras_json=excluded.extras_json,
          data_version=excluded.data_version
        """,
        (
            cid,
            ih,
            status,
            json.dumps(match_refs, ensure_ascii=False),
            score,
            json.dumps(diff or [], ensure_ascii=False),
            json.dumps(extra or {}, ensure_ascii=False),
            DATA_VERSION,
        ),
    )
    conn.commit()
    return cid


def get_card(conn: sqlite3.Connection, cid: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM cards WHERE id = ?", (cid,)).fetchone()
    if not row:
        return None
    keys = row.keys()
    raw_diff = row["diff_json"] if "diff_json" in keys else "[]"
    raw_extra = row["extras_json"] if "extras_json" in keys else "{}"
    extras = json.loads(raw_extra or "{}")
    return {
        "id": row["id"],
        "input_hash": row["input_hash"],
        "status": row["status"],
        "match_refs": json.loads(row["match_refs"]),
        "score": row["score"],
        "diff": json.loads(raw_diff or "[]"),
        "diff_highlight": extras.get("diff_highlight") or [],
        "user_diff_highlight": extras.get("user_diff_highlight") or [],
        "correct_text": extras.get("correct_text"),
        "matched_span": extras.get("matched_span"),
        "gradings": extras.get("gradings") or [],
        "data_version": row["data_version"],
        "created_at": row["created_at"],
    }
