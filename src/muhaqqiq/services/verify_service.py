"""Verify + upsert card orchestration."""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import Request

from muhaqqiq import DATA_VERSION
from muhaqqiq.api.deps import request_id
from muhaqqiq.domain.status import STATUS_AR
from muhaqqiq.observability import record_verify
from muhaqqiq.repositories.cards_repo import upsert_card
from muhaqqiq.repositories.sqlite_repo import connect
from muhaqqiq.services.match_service import match

logger = logging.getLogger("muhaqqiq")


def verify_text(text: str, *, request: Request | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    conn = connect()
    try:
        result = match(conn, text)
        cid = upsert_card(
            conn,
            status=result["status"],
            norm_skeleton=result["norm_skeleton"],
            match_refs=result["matches"],
            score=result["score"],
            diff=result.get("diff") or [],
            extra={
                "diff_highlight": result.get("diff_highlight") or [],
                "user_diff_highlight": result.get("user_diff_highlight") or [],
                "correct_text": result.get("correct_text"),
                "matched_span": result.get("matched_span"),
                "gradings": result.get("gradings") or [],
            },
        )
        latency = (time.perf_counter() - started) * 1000
        record_verify(result["status"], latency)
        logger.info(
            "verify rid=%s status=%s score=%s card_id=%s latency_ms=%.1f",
            request_id(request),
            result["status"],
            result["score"],
            cid,
            latency,
        )
        return {
            "card_id": cid,
            "status": result["status"],
            "status_ar": STATUS_AR.get(result["status"], result["status"]),
            "matches": result["matches"],
            "diff": result["diff"],
            "diff_highlight": result.get("diff_highlight") or [],
            "user_diff_highlight": result.get("user_diff_highlight") or [],
            "correct_text": result.get("correct_text"),
            "matched_span": result.get("matched_span"),
            "gradings": result.get("gradings") or [],
            "score": result["score"],
            "claims": result.get("claims") or [],
            "primary_claim_index": result.get("primary_claim_index", 0),
            "card_url": f"/c/{cid}",
            "data_version": DATA_VERSION,
            "ai_disclosure": "AI-assisted tool, not a fatwa authority.",
            "supported_means": (
                "Supported means the text was found in an approved source; "
                "it does not mean the surrounding claim or its application is correct."
            ),
            "reply_template_key": {
                "CLOSE_WITH_DIFF": "close",
                "ATTRIBUTED_RULING": "attributed",
                "SUPPORTED": "supported_copy",
            }.get(result["status"]),
        }
    finally:
        conn.close()
