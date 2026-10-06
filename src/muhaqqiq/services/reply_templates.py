"""Fixed polite-reply templates — never LLM-generated."""

from __future__ import annotations

from typing import Any

# Placeholders: {correct_text}, {reference}, {proof_url}, {card_url}, {grader}, {grade}
TEMPLATES: dict[str, dict[str, dict[str, str]]] = {
    "close": {
        "ar": {
            "full": (
                "جزاك الله خيراً، وجدتُ أن النص في المصدر هكذا: «{correct_text}» "
                "({reference}). للتفاصيل: {card_url}"
            ),
            "short": "جزاك الله خيراً، النص الصحيح: «{correct_text}» ({reference})",
        },
        "en": {
            "full": (
                "Jazakallahu khayran — the source text is: «{correct_text}» "
                "({reference}). Details: {card_url}"
            ),
            "short": "The correct text is: «{correct_text}» ({reference})",
        },
        "tr": {
            "full": (
                "Allah razı olsun — kaynak metin şöyle: «{correct_text}» "
                "({reference}). Ayrıntılar: {card_url}"
            ),
            "short": "Doğru metin: «{correct_text}» ({reference})",
        },
    },
    "attributed": {
        "ar": {
            "full": (
                "جزاك الله خيراً، هذا اللفظ يُنسب بحكم مخزّن: حكم {grader}: {grade} "
                "({reference}). البطاقة: {card_url}"
            ),
            "short": "حكم {grader}: {grade} ({reference}) — {card_url}",
        },
        "en": {
            "full": (
                "Jazakallahu khayran — a stored ruling attributes this wording: "
                "Ruling of {grader}: {grade} ({reference}). Card: {card_url}"
            ),
            "short": "Ruling of {grader}: {grade} ({reference})",
        },
        "tr": {
            "full": (
                "Allah razı olsun — kayıtlı hüküm: {grader} hükmü: {grade} "
                "({reference}). Kart: {card_url}"
            ),
            "short": "{grader} hükmü: {grade} ({reference})",
        },
    },
    "supported_copy": {
        "ar": {
            "full": "النص في المصدر: «{correct_text}» ({reference}). {proof_url}",
            "short": "«{correct_text}» ({reference})",
        },
        "en": {
            "full": "Source text: «{correct_text}» ({reference}). {proof_url}",
            "short": "«{correct_text}» ({reference})",
        },
        "tr": {
            "full": "Kaynak metin: «{correct_text}» ({reference}). {proof_url}",
            "short": "«{correct_text}» ({reference})",
        },
    },
}


def fill_template(
    kind: str,
    lang: str,
    *,
    variant: str = "full",
    fields: dict[str, Any],
) -> str | None:
    """Fill a fixed template from stored fields only. Returns None if unavailable."""
    block = TEMPLATES.get(kind, {}).get(lang) or TEMPLATES.get(kind, {}).get("ar")
    if not block:
        return None
    tpl = block.get(variant) or block.get("full")
    if not tpl:
        return None
    safe = {k: ("" if v is None else str(v)) for k, v in fields.items()}
    try:
        return tpl.format_map(_SafeMap(safe))
    except (KeyError, ValueError):
        return None


class _SafeMap(dict):
    def __missing__(self, key: str) -> str:
        return ""


def templates_payload() -> dict[str, Any]:
    """Static map for clients that fill placeholders themselves."""
    return TEMPLATES
