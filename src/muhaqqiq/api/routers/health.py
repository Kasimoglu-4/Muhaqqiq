"""Health and ops endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from muhaqqiq import DATA_VERSION, __version__
from muhaqqiq.observability import ops_summary
from muhaqqiq.repositories.embeddings import DEFAULT_EMBEDDINGS
from muhaqqiq.repositories.sqlite_repo import connect, data_version, db_path
from muhaqqiq.services.ocr_service import ocr_spend_snapshot

router = APIRouter(tags=["ops"])


@router.get("/health")
def health() -> dict[str, Any]:
    path = db_path()
    verse_count = hadith_count = 0
    if path.exists():
        conn = connect()
        try:
            verse_count = conn.execute("SELECT COUNT(*) FROM quran_verses").fetchone()[0]
            hadith_count = conn.execute("SELECT COUNT(*) FROM hadiths").fetchone()[0]
        finally:
            conn.close()
    return {
        "ok": True,
        "version": __version__,
        "data_version": data_version() or DATA_VERSION,
        "db": str(path),
        "quran_verses": verse_count,
        "hadiths": hadith_count,
        "embeddings": DEFAULT_EMBEDDINGS.enabled() and DEFAULT_EMBEDDINGS._loaded,
        "ops": ops_summary(ocr_spend=ocr_spend_snapshot()),
    }


@router.get("/v1/ops/summary", summary="In-process metrics for beta dashboards")
def ops_endpoint() -> dict[str, Any]:
    return ops_summary(ocr_spend=ocr_spend_snapshot())
