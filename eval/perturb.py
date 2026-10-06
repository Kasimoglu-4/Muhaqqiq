"""Text perturbation helpers for benchmark expansion (Phase 5.2)."""

from __future__ import annotations

import re

_TASHKEEL = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")

# Common OCR / keyboard confusions (Arabic)
_OCR_MAP = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
    }
)


def strip_tashkeel(text: str) -> str:
    return _TASHKEEL.sub("", text)


def add_tashkeel_light(text: str) -> str:
    """Add a few common marks so OCR/tashkeel variants stay in the set."""
    if "ا" not in text:
        return text
    return text.replace("ا", "َا", 1)


def swap_heh_teh(text: str) -> str:
    return text.replace("ة", "ه").replace("ه\u200c", "ة")


def swap_yaa_alef_maqsura(text: str) -> str:
    return text.replace("ى", "ي").replace("ي", "ى", 1) if "ي" in text else text.replace("ى", "ي")


def ocr_confusions(text: str) -> str:
    return text.translate(_OCR_MAP)


def truncate_words(text: str, keep: int) -> str:
    words = text.split()
    if len(words) <= keep:
        return text
    return " ".join(words[:keep])


def delete_middle_word(text: str) -> str:
    words = text.split()
    if len(words) < 3:
        return text
    i = len(words) // 2
    return " ".join(words[:i] + words[i + 1 :])


def replace_middle_word(text: str, replacement: str = "شيء") -> str:
    words = text.split()
    if len(words) < 3:
        return text
    i = len(words) // 2
    words[i] = replacement
    return " ".join(words)


def insert_word(text: str, word: str = "أيضا") -> str:
    words = text.split()
    if len(words) < 2:
        return f"{text} {word}"
    i = max(1, len(words) // 2)
    words.insert(i, word)
    return " ".join(words)


def add_forward_spam(text: str) -> str:
    return f"{text} انشرها في كل مكان ولا تبخل"


def add_question_wrapper(text: str) -> str:
    return f"ما حكم من قال: {text}؟"


def ask_for_proving_hadith(claim: str) -> str:
    return f"أعطني حديثا يثبت أن {claim}"


def whatsapp_prefix(text: str) -> str:
    return f"مشاركة من واتساب:\n{text}"


def linebreak_join(text: str) -> str:
    """Simulate OCR line breaks mid-phrase."""
    words = text.split()
    if len(words) < 4:
        return text
    mid = len(words) // 2
    return " ".join(words[:mid]) + "\n" + " ".join(words[mid:])


def multi_aya_glue(a: str, b: str) -> str:
    return f"{a} {b}"
