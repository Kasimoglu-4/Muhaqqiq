"""Claim detection and segmentation (Phase 2.1)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from muhaqqiq.domain.normalize import FORWARD_SPAM

QUOTE_SPLIT = re.compile(r"[﴿﴾«»\"\n]+")
VERSE_MARKERS = re.compile(r"[﴿﴾]|سورة\s+\S+|الآية|بسم الله")
HADITH_MARKERS = re.compile(
    r"قال\s+رسول\s+الله|قال\s+النبي|صلى الله عليه وسلم|رواه\s+\S+|متفق عليه|في الصحيح"
)
ATHAR_MARKERS = re.compile(
    r"قال\s+(علي|عمر|عثمان|ابو بكر|أبو بكر|ابن عباس|عائشة|معاذ)\b"
)


@dataclass(frozen=True)
class ClaimSpan:
    text: str
    start: int
    end: int
    claim_type: str  # verse | hadith | athar | unknown


def _tag(text: str) -> str:
    if VERSE_MARKERS.search(text):
        return "verse"
    if HADITH_MARKERS.search(text):
        return "hadith"
    if ATHAR_MARKERS.search(text):
        return "athar"
    return "unknown"


def _strip_spam(text: str) -> str:
    return FORWARD_SPAM.sub(" ", text).strip()


def segment(text: str) -> list[ClaimSpan]:
    """Split messy forwarded text into claim spans with rule-based types."""
    if not text or not text.strip():
        return []

    spans: list[ClaimSpan] = []
    last = 0
    for m in QUOTE_SPLIT.finditer(text):
        chunk = text[last : m.start()]
        cleaned = _strip_spam(chunk)
        if cleaned:
            # Include surrounding delimiters so ﴿...﴾ tags as verse
            context = text[max(0, last - 2) : min(len(text), m.end() + 2)]
            start = last + chunk.find(cleaned[0])
            end = last + len(chunk.rstrip())
            spans.append(ClaimSpan(cleaned, max(start, last), end, _tag(context)))
        last = m.end()
    tail = text[last:]
    cleaned = _strip_spam(tail)
    if cleaned:
        context = text[max(0, last - 2) :]
        start = last + (tail.find(cleaned[0]) if cleaned else 0)
        spans.append(ClaimSpan(cleaned, start, start + len(tail.rstrip()), _tag(context)))

    merged: list[ClaimSpan] = []
    for span in spans:
        if len(span.text.split()) < 2 and merged:
            prev = merged[-1]
            merged[-1] = ClaimSpan(
                f"{prev.text} {span.text}".strip(),
                prev.start,
                span.end,
                prev.claim_type if prev.claim_type != "unknown" else span.claim_type,
            )
        elif span.text.strip():
            merged.append(span)

    if not merged:
        cleaned = _strip_spam(text)
        if cleaned:
            merged = [ClaimSpan(cleaned, 0, len(text), _tag(text))]
    return merged
