"""Card JSON, HTML, and OG image."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from muhaqqiq.card_image import render_og_png
from muhaqqiq.domain.status import STATUS_AR
from muhaqqiq.repositories.sqlite_repo import connect
from muhaqqiq.services.card_service import card_page_payload, load_card

router = APIRouter()
TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))


@router.get("/v1/cards/{card_id}", tags=["cards"])
def card_json(card_id: str) -> dict:
    conn = connect()
    try:
        card = load_card(conn, card_id)
    finally:
        conn.close()
    if not card:
        raise HTTPException(404, "Card not found")
    return card


@router.get("/c/{card_id}", response_class=HTMLResponse, include_in_schema=False)
def card_page(request: Request, card_id: str) -> HTMLResponse:
    conn = connect()
    try:
        card = load_card(conn, card_id)
    finally:
        conn.close()
    if not card:
        raise HTTPException(404, "Card not found")
    result = card_page_payload(card)
    status_ar = result["status_ar"]
    return TEMPLATES.TemplateResponse(
        request,
        "card.html",
        {
            "title": "بطاقة التحقق",
            "result": result,
            "user_text": None,
            "og_title": f"مُحقِّق — {status_ar}",
            "og_description": "بطاقة تحقق لنص منسوب للقرآن أو الحديث",
            "og_image": f"/c/{card_id}/og.png",
        },
    )


@router.get("/c/{card_id}/og.png", include_in_schema=False)
def card_og_png(card_id: str):
    conn = connect()
    try:
        card = load_card(conn, card_id)
    finally:
        conn.close()
    if not card:
        raise HTTPException(404, "Card not found")
    status_ar = STATUS_AR.get(card["status"], card["status"])
    png = render_og_png(
        status_ar=status_ar,
        status=card["status"],
        card_id=card_id,
        match_refs=card.get("match_refs"),
        correct_text=card.get("correct_text"),
    )
    return Response(png, media_type="image/png")
