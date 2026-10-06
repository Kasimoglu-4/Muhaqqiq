"""Lightweight OG / share PNG (Pillow). Full RTL shaping stays in the Playwright worker."""

from __future__ import annotations

import io
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

STATUS_COLORS = {
    "SUPPORTED": (47, 157, 98),
    "CLOSE_WITH_DIFF": (196, 154, 60),
    "ATTRIBUTED_RULING": (138, 107, 90),
    "UNDETERMINED": (120, 130, 122),
}


def _font(size: int) -> ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _quote_and_source(match_refs: list[dict[str, Any]] | None, correct_text: str | None) -> tuple[str, str]:
    match = (match_refs or [None])[0] or {}
    quote = (correct_text or match.get("text") or match.get("correct_text") or "").strip()
    if len(quote) > 90:
        quote = quote[:90].rstrip() + "…"
    if quote and not quote.startswith(("«", '"', "“")):
        quote = f"«{quote}»"

    kind = match.get("kind") or ""
    ref = match.get("ref") or {}
    if kind == "quran":
        source = f"Quran · {ref.get('sura')}:{ref.get('aya')}"
    elif kind in {"hadith", "enc_hadith"}:
        collection = ref.get("collection") or ref.get("source") or "Hadith"
        number = ref.get("number")
        source = f"{collection}, {number}" if number else str(collection)
    else:
        source = str(ref.get("claim_type") or kind or "")
    return quote, source


def render_og_png(
    *,
    status_ar: str,
    status: str,
    card_id: str,
    match_refs: list[dict[str, Any]] | None = None,
    correct_text: str | None = None,
) -> bytes:
    if status == "SUPPORTED":
        return _render_supported_card(
            status_ar=status_ar,
            card_id=card_id,
            match_refs=match_refs,
            correct_text=correct_text,
        )

    img = Image.new("RGB", (1200, 630), (15, 26, 20))
    draw = ImageDraw.Draw(img)
    accent = STATUS_COLORS.get(status, (196, 163, 90))
    draw.rectangle((0, 0, 1200, 12), fill=accent)
    draw.rectangle((0, 618, 1200, 630), fill=accent)

    title_font = _font(72)
    body_font = _font(36)
    small_font = _font(28)

    draw.text((80, 120), "Muhaqqiq", fill=(196, 163, 90), font=title_font)
    draw.text((80, 240), status_ar, fill=(242, 245, 240), font=body_font)
    draw.text((80, 320), status, fill=(183, 196, 186), font=small_font)
    draw.text(
        (80, 480),
        f"card /c/{card_id} · AI-assisted, not a fatwa",
        fill=(183, 196, 186),
        font=small_font,
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _render_supported_card(
    *,
    status_ar: str,
    card_id: str,
    match_refs: list[dict[str, Any]] | None,
    correct_text: str | None,
) -> bytes:
    """White share card on dark green — matches the product share mock."""
    img = Image.new("RGB", (1200, 630), (15, 26, 20))
    draw = ImageDraw.Draw(img)

    # Card panel
    card = (90, 70, 1110, 560)
    draw.rounded_rectangle(card, radius=40, fill=(255, 255, 255))

    green = STATUS_COLORS["SUPPORTED"]
    title_font = _font(40)
    quote_font = _font(44)
    meta_font = _font(30)
    small_font = _font(24)

    # Check (left) + status (right) — matches share mock
    cx, cy, r = 180, 145, 34
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=green)
    draw.line((cx - 14, cy + 2, cx - 4, cy + 12), fill=(255, 255, 255), width=5)
    draw.line((cx - 4, cy + 12, cx + 16, cy - 10), fill=(255, 255, 255), width=5)
    draw.text((1060, 120), status_ar, fill=green, font=title_font, anchor="ra")

    quote, source = _quote_and_source(match_refs, correct_text)
    y = 220
    if quote:
        for line in textwrap.wrap(quote, width=36)[:3]:
            draw.text((1060, y), line, fill=(20, 22, 20), font=quote_font, anchor="ra")
            y += 58
    else:
        draw.text((1060, y), status_ar, fill=(20, 22, 20), font=quote_font, anchor="ra")
        y += 58

    kind = "حديث نبوي"
    m0 = (match_refs or [{}])[0] or {}
    if m0.get("kind") == "quran":
        kind = "آية قرآنية"
    draw.text((1060, y + 24), kind, fill=(122, 132, 125), font=meta_font, anchor="ra")
    if source:
        draw.text((1060, y + 70), source, fill=(122, 132, 125), font=meta_font, anchor="ra")

    # CTA bar
    draw.rounded_rectangle((140, 455, 1060, 520), radius=20, fill=(220, 239, 227))
    draw.text((600, 488), "عرض المصدر والإسناد", fill=(20, 32, 24), font=meta_font, anchor="mm")
    draw.text((600, 545), f"/c/{card_id}", fill=(150, 160, 152), font=small_font, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
