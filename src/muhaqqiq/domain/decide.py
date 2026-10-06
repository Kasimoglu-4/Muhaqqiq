"""Deterministic status decision. Thresholds calibrated on DEV; verify on holdout."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Defaults; verify on holdout after any change (FS must stay 0).
# Dev grid may suggest lower T_EXACT; do not apply if holdout FS > 0.
T_EXACT = 92.0
T_CLOSE = 70.0
T_KNOWN = 88.0
M_MIN = 2.0


@dataclass
class Candidate:
    kind: str  # quran | hadith | known_claim
    id: int
    score: float
    exact: bool
    text_display: str
    norm: str
    ref: dict[str, Any]
    has_grading: bool = False
    grading: dict[str, Any] | None = None


def decide(best: Candidate | None, second_score: float | None, n_words: int) -> str:
    if best is None:
        return "UNDETERMINED"

    margin = best.score - (second_score if second_score is not None else 0.0)

    if best.kind in {"known_claim", "enc_hadith"} and best.score >= T_KNOWN:
        return "ATTRIBUTED_RULING"

    # Single-token queries: only a full exact match is a quote.
    # Substring hits like «خيركم» inside a long matn must never Support.
    if n_words < 2:
        strong_quote = best.exact
    else:
        strong_quote = best.exact or best.score >= 99.0

    # Short inputs: abstain unless exact / contiguous quote (score >= 99)
    if n_words < 4 and not strong_quote:
        return "UNDETERMINED"

    # Quran/hadith Supported only for exact or contiguous quote (score>=99)
    if best.kind in {"hadith", "quran"} and not strong_quote and best.score >= T_EXACT:
        return "CLOSE_WITH_DIFF"

    strong = strong_quote or margin >= M_MIN
    if best.score >= T_EXACT and strong:
        if best.has_grading:
            return "ATTRIBUTED_RULING"
        return "SUPPORTED"

    if T_CLOSE <= best.score < T_EXACT:
        return "CLOSE_WITH_DIFF"

    return "UNDETERMINED"
