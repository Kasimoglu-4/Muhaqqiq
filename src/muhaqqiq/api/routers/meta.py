"""Sources, feedback, reply templates."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Request

from muhaqqiq.api.deps import request_id
from muhaqqiq.api.middleware import verify_turnstile
from muhaqqiq.repositories.sources_repo import list_sources
from muhaqqiq.repositories.sqlite_repo import connect
from muhaqqiq.schemas.feedback import FeedbackBody
from muhaqqiq.services.reply_templates import templates_payload

logger = logging.getLogger("muhaqqiq")
router = APIRouter(tags=["meta"])


@router.get("/v1/sources")
def sources() -> dict:
    conn = connect()
    try:
        return list_sources(conn)
    finally:
        conn.close()


@router.get("/v1/reply-templates")
def reply_templates() -> dict:
    return {"templates": templates_payload()}


@router.post("/v1/feedback", summary="Anonymous feedback (rate-limited)")
async def feedback(body: FeedbackBody, request: Request) -> dict[str, str]:
    await verify_turnstile(
        body.turnstile_token, request.client.host if request.client else None
    )
    fid = uuid.uuid4().hex[:12]
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO feedback (id, card_id, kind, comment) VALUES (?, ?, ?, ?)",
            (fid, body.card_id, body.kind, (body.comment or "")[:500]),
        )
        conn.commit()
    finally:
        conn.close()
    logger.info("feedback rid=%s kind=%s card_id=%s", request_id(request), body.kind, body.card_id)
    return {"ok": "true", "id": fid}
