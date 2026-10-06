"""Shared download helpers for pinned sources."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MANIFEST = RAW / "download_manifest.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(follow_redirects=True, timeout=120.0) as client:
        r = client.get(url)
        r.raise_for_status()
        dest.write_bytes(r.content)
    return {
        "url": url,
        "path": str(dest.relative_to(ROOT)).replace("\\", "/"),
        "sha256": sha256_bytes(r.content),
        "retrieved_at": datetime.now(UTC).date().isoformat(),
        "bytes": len(r.content),
    }


def update_manifest(entries: list[dict]) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    existing: dict[str, dict] = {}
    if MANIFEST.exists():
        for item in json.loads(MANIFEST.read_text(encoding="utf-8")):
            existing[item["path"]] = item
    for entry in entries:
        existing[entry["path"]] = entry
    MANIFEST.write_text(
        json.dumps(list(existing.values()), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
