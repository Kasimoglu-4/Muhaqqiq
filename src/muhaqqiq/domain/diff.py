"""Character-level diff and highlight segments for result cards."""

from __future__ import annotations

import difflib
import re
import unicodedata
from typing import Any

# Arabic tashkeel / Quranic marks / tatweel — stripped in normalize, kept in display.
_MARKS = re.compile(r"[\u064B-\u065F\u0670\u06D6-\u06ED\u08D4-\u08FF\u0640]")


def char_diff(user_norm: str, original_norm: str) -> list[dict[str, Any]]:
    """Return opcodes mapped to span dicts for the card UI."""
    sm = difflib.SequenceMatcher(a=user_norm, b=original_norm, autojunk=False)
    out: list[dict[str, Any]] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        op = {"replace": "replace", "delete": "delete", "insert": "insert"}[tag]
        out.append(
            {
                "op": op,
                "user_span": {"start": i1, "end": i2, "text": user_norm[i1:i2]},
                "original_span": {"start": j1, "end": j2, "text": original_norm[j1:j2]},
            }
        )
    return out


def _letter_key(ch: str) -> str:
    ch = unicodedata.normalize("NFKC", ch)
    if _MARKS.match(ch) or ch.isspace():
        return ""
    ch = ch.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ٱ", "ا")
    ch = ch.replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي").replace("ء", "")
    ch = ch.replace("ة", "ه")
    if not re.match(r"\w", ch, flags=re.UNICODE):
        return ""
    return ch


def _display_letter_points(display: str) -> list[tuple[int, int, str]]:
    """(start, end_exclusive, key) for each letter in display, absorbing following marks."""
    points: list[tuple[int, int, str]] = []
    i = 0
    n = len(display)
    while i < n:
        key = _letter_key(display[i])
        if not key:
            i += 1
            continue
        start = i
        i += 1
        while i < n and _MARKS.match(display[i]):
            i += 1
        points.append((start, i, key))
    return points


def _norm_letter_indices(norm: str) -> list[int]:
    """Norm indices that are letters (skip spaces)."""
    return [i for i, ch in enumerate(norm) if not ch.isspace()]


def _map_norm_to_display(display: str, norm: str) -> list[tuple[int, int] | None]:
    """Map each norm index → display (start, end) or None for spaces / unmapped."""
    out: list[tuple[int, int] | None] = [None] * len(norm)
    points = _display_letter_points(display)
    n_idx = _norm_letter_indices(norm)
    if not points or not n_idx:
        return out

    disp_keys = "".join(p[2] for p in points)
    norm_keys = "".join(norm[i] for i in n_idx)

    # Align letter streams with SequenceMatcher (handles small orthography gaps).
    sm = difflib.SequenceMatcher(a=norm_keys, b=disp_keys, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            continue
        for k in range(i2 - i1):
            ni = n_idx[i1 + k]
            start, end, _ = points[j1 + k]
            out[ni] = (start, end)
    return out


def _slice_mapped(
    mapping: list[tuple[int, int] | None],
    display: str,
    j1: int,
    j2: int,
    fallback: str,
) -> str:
    spans = [mapping[j] for j in range(j1, j2) if mapping[j] is not None]
    if not spans:
        return fallback
    start = spans[0][0]
    end = spans[-1][1]
    # Extend through trailing whitespace / marks before next letter after segment.
    while end < len(display) and (display[end].isspace() or _MARKS.match(display[end])):
        end += 1
    return display[start:end]


def diff_highlight(original_display: str, user_norm: str, original_norm: str) -> list[dict[str, Any]]:
    """Colored segments over the *stored* original display text.

    - equal → matching wording (green)
    - insert → extra wording in the source (amber)
    - replace → spelling / letter difference (rose)
    - insert_marker → present in user, missing from source
    """
    if not original_norm:
        return [{"op": "equal", "text": original_display}] if original_display else []

    mapping = _map_norm_to_display(original_display, original_norm) if original_display else []
    use_display = bool(original_display) and any(m is not None for m in mapping)
    base = original_display if use_display else original_norm

    sm = difflib.SequenceMatcher(a=user_norm, b=original_norm, autojunk=False)
    segments: list[dict[str, Any]] = []
    for tag, _i1, _i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            if j1 >= j2:
                continue
            text = (
                _slice_mapped(mapping, base, j1, j2, original_norm[j1:j2])
                if use_display
                else base[j1:j2]
            )
            if text:
                segments.append({"op": "equal", "text": text})
            continue
        if tag == "delete":
            segments.append({"op": "insert_marker", "text": ""})
            continue
        if tag == "insert":
            text = (
                _slice_mapped(mapping, base, j1, j2, original_norm[j1:j2])
                if use_display
                else base[j1:j2]
            )
            if text:
                segments.append({"op": "insert", "text": text})
            continue
        if tag == "replace":
            text = (
                _slice_mapped(mapping, base, j1, j2, original_norm[j1:j2])
                if use_display
                else base[j1:j2]
            )
            if text:
                segments.append({"op": "replace", "text": text})
    return segments


def user_diff_highlight(user_display: str, user_norm: str, original_norm: str) -> list[dict[str, Any]]:
    """Highlight segments over the *user* display text."""
    if not user_norm:
        return [{"op": "equal", "text": user_display}] if user_display else []

    mapping = _map_norm_to_display(user_display, user_norm) if user_display else []
    use_display = bool(user_display) and any(m is not None for m in mapping)
    base = user_display if use_display else user_norm

    sm = difflib.SequenceMatcher(a=user_norm, b=original_norm, autojunk=False)
    segments: list[dict[str, Any]] = []
    for tag, i1, i2, _j1, _j2 in sm.get_opcodes():
        if tag == "equal":
            if i1 >= i2:
                continue
            text = (
                _slice_mapped(mapping, base, i1, i2, user_norm[i1:i2])
                if use_display
                else base[i1:i2]
            )
            if text:
                segments.append({"op": "equal", "text": text})
            continue
        if tag == "insert":
            continue
        if tag in {"delete", "replace"}:
            text = (
                _slice_mapped(mapping, base, i1, i2, user_norm[i1:i2])
                if use_display
                else base[i1:i2]
            )
            if text:
                segments.append({"op": "replace", "text": text})
    return segments
