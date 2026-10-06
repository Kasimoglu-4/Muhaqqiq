"""Verify text / image endpoints."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.datastructures import UploadFile as StarletteUploadFile

from muhaqqiq.api.middleware import verify_turnstile
from muhaqqiq.schemas.verify import VerifyBody
from muhaqqiq.services.ocr_service import MAX_IMAGE_BYTES, run_ocr
from muhaqqiq.services.verify_service import verify_text

router = APIRouter()
TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))


async def _ocr_payload(image: UploadFile, request: Request) -> dict[str, Any]:
    data = await image.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "Image exceeds 5 MB limit")
    try:
        # Windows OCR uses asyncio.run internally — must not run on the ASGI loop.
        ocr = await asyncio.to_thread(run_ocr, data, image.content_type or "")
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {
        "extracted_text": ocr.text,
        "confidence": ocr.confidence,
        "provider": ocr.provider,
        "editable": True,
        "next": "POST /v1/verify with corrected text",
        "ai_disclosure": "AI-assisted tool, not a fatwa authority.",
    }


@router.post(
    "/v1/verify",
    tags=["verify"],
    summary="Verify text (JSON) or OCR image (multipart)",
)
async def verify_api(request: Request) -> dict[str, Any]:
    ct = (request.headers.get("content-type") or "").lower()
    if "multipart/form-data" in ct or "application/x-www-form-urlencoded" in ct:
        form = await request.form()
        token = form.get("turnstile_token")
        await verify_turnstile(
            token if isinstance(token, str) else None,
            request.client.host if request.client else None,
        )
        text_val = form.get("text")
        text = text_val.strip() if isinstance(text_val, str) else ""
        image = form.get("image")
        if text:
            if len(text) > 2000:
                raise HTTPException(400, "Text too long")
            return verify_text(text, request=request)
        if isinstance(image, (UploadFile, StarletteUploadFile)):
            return await _ocr_payload(image, request)
        raise HTTPException(400, "Provide text or image")

    try:
        body = VerifyBody.model_validate(await request.json())
    except Exception as e:
        raise HTTPException(400, "Invalid JSON body; expected {text}") from e
    await verify_turnstile(
        body.turnstile_token, request.client.host if request.client else None
    )
    return verify_text(body.text, request=request)


@router.post(
    "/v1/verify/image",
    tags=["verify"],
    summary="OCR image then return extracted text for user correction",
    deprecated=True,
)
async def verify_image(
    request: Request,
    image: UploadFile = File(...),  # noqa: B008
    turnstile_token: str | None = Form(None),
) -> dict[str, Any]:
    await verify_turnstile(turnstile_token, request.client.host if request.client else None)
    return await _ocr_payload(image, request)


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(request, "home.html", {"title": "مُحقِّق"})


@router.post("/verify", response_class=HTMLResponse, include_in_schema=False)
async def verify_form(
    request: Request,
    text: str = Form(""),
    image: UploadFile | None = File(None),  # noqa: B008
) -> HTMLResponse:
    if (not text.strip()) and image is not None and image.filename:
        data = await image.read()
        if data:
            try:
                ocr = await asyncio.to_thread(run_ocr, data, image.content_type or "")
            except ValueError as e:
                raise HTTPException(400, str(e)) from e
            return TEMPLATES.TemplateResponse(
                request,
                "home.html",
                {
                    "title": "راجع النص المستخرج",
                    "ocr_text": ocr.text,
                    "ocr_message": (
                        "راجع النص المستخرج ثم اضغط تحقق."
                        if ocr.text.strip()
                        else "لم يُستخرج نص. الصق النص يدويًا."
                    ),
                },
            )

    if not text or not text.strip():
        raise HTTPException(400, "Text required")
    if len(text) > 2000:
        raise HTTPException(400, "Text too long")
    result = verify_text(text, request=request)
    return TEMPLATES.TemplateResponse(
        request,
        "card.html",
        {"title": "نتيجة التحقق", "result": result, "user_text": text},
    )
