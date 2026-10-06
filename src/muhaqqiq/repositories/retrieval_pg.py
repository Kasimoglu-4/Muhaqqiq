"""Postgres pg_trgm shortlist (Phase 2.2 stage 2)."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("muhaqqiq.retrieval_pg")


def pg_url() -> str | None:
    return os.environ.get("DATABASE_URL") or os.environ.get("MUHAQQIQ_PG_URL")


def trigram_shortlist(
    skeleton: str,
    *,
    kind: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return top-N rows by word/trigram similarity. Empty if Postgres unavailable."""
    url = pg_url()
    if not url or not skeleton or len(skeleton) < 4:
        return []
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        return []

    # word_similarity handles short queries inside long hadith (isnad + matn)
    if kind == "quran":
        sql = """
            SELECT id, sura, aya, text_uthmani, norm_skeleton,
                   greatest(
                     similarity(norm_skeleton, %s),
                     word_similarity(%s, norm_skeleton)
                   ) AS sim
            FROM quran_verses
            WHERE norm_skeleton LIKE '%%' || %s || '%%'
               OR %s LIKE '%%' || norm_skeleton || '%%'
               OR word_similarity(%s, norm_skeleton) > 0.3
            ORDER BY sim DESC NULLS LAST
            LIMIT %s
        """
        params = (skeleton, skeleton, skeleton, skeleton, skeleton, limit)
    elif kind == "hadith":
        sql = """
            SELECT id, collection, number, text_ar, norm_skeleton,
                   greatest(
                     similarity(norm_skeleton, %s),
                     word_similarity(%s, norm_skeleton)
                   ) AS sim
            FROM hadiths
            WHERE norm_skeleton LIKE '%%' || %s || '%%'
               OR word_similarity(%s, norm_skeleton) > 0.35
            ORDER BY sim DESC NULLS LAST
            LIMIT %s
        """
        params = (skeleton, skeleton, skeleton, skeleton, limit)
    elif kind == "known_claim":
        sql = """
            SELECT c.id, c.text_ar, c.norm_skeleton, c.claim_type,
                   r.grader, r.ruling, r.reference, r.url,
                   greatest(
                     similarity(c.norm_skeleton, %s),
                     word_similarity(%s, c.norm_skeleton)
                   ) AS sim
            FROM known_claims c
            LEFT JOIN known_claim_rulings r ON r.claim_id = c.id
            WHERE c.norm_skeleton LIKE '%%' || %s || '%%'
               OR word_similarity(%s, c.norm_skeleton) > 0.35
            ORDER BY sim DESC NULLS LAST
            LIMIT %s
        """
        params = (skeleton, skeleton, skeleton, skeleton, limit)
    else:
        return []

    try:
        with psycopg.connect(url, row_factory=dict_row) as conn, conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            cur.execute(sql, params)
            rows = list(cur.fetchall())
            return [r for r in rows if float(r.get("sim") or 0) >= 0.2]
    except Exception as exc:  # noqa: BLE001 — soft-fail when PG down/misconfigured
        logger.debug("trigram_shortlist failed: %s", exc)
        return []
