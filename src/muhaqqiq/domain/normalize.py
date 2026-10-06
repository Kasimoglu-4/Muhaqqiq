"""Arabic text normalization for matching (never mutate display text)."""

from __future__ import annotations

import re
import unicodedata

# Note: U+0670 (superscript alef) is expanded to ا before stripping marks
TASHKEEL = re.compile(r"[\u064B-\u065F\u06D6-\u06ED\u08D3-\u08FF]")
SUPERSCRIPT_ALEF = "\u0670"
TATWEEL = "\u0640"
HONORIFICS = re.compile(
    r"(ﷺ|صلى الله عليه وسلم|صلي الله عليه وسلم|عليه الصلاة والسلام|رضي الله عنه[ما]?)"
)
NOISE = re.compile(
    r"https?://\S+|[\u200c-\u200f\u202a-\u202e]|[\U0001F300-\U0001FAFF]|[﴿﴾«»\"'\[\]\(\)\*_~]"
)
FORWARD_SPAM = re.compile(
    r"(انشرها|انشرها للجميع|ولا تبخل|لا تنس|أعد إرسال|forward this)",
    re.IGNORECASE,
)

__all__ = ["FORWARD_SPAM", "normalize", "strip_bidi", "word_count"]
BIDI_CONTROLS = re.compile(r"[\u200c-\u200f\u202a-\u202e]")


def strip_bidi(text: str) -> str:
    """Remove bidirectional control chars from stored display text (not content)."""
    return BIDI_CONTROLS.sub("", text)


def normalize(text: str, *, fuzzy: bool = True) -> str:
    t = unicodedata.normalize("NFKC", text)
    t = NOISE.sub(" ", t)
    t = HONORIFICS.sub(" ", t)
    t = FORWARD_SPAM.sub(" ", t)
    t = t.replace(SUPERSCRIPT_ALEF, "ا")
    t = TASHKEEL.sub("", t).replace(TATWEEL, "")
    t = re.sub("[أإآٱ]", "ا", t)
    t = t.replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي").replace("ء", "")
    if fuzzy:
        t = t.replace("ة", "ه")
        # Tanzil orthography uses الرحمان (superscript alef); users type الرحمن
        t = re.sub(r"الرحم[ا]?ن", "الرحمان", t)
        # Quranic / typed variants: اشكوا↔اشكو، قالوا↔قالو (trailing وا)
        t = re.sub(r"وا\b", "و", t)
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def word_count(norm: str) -> int:
    if not norm:
        return 0
    return len(norm.split())
