"""Card read/enrichment use-cases."""

from __future__ import annotations

import sqlite3
from typing import Any

from muhaqqiq.domain.status import STATUS_AR
from muhaqqiq.repositories.cards_repo import get_card


def load_card(conn: sqlite3.Connection, card_id: str) -> dict[str, Any] | None:
    card = get_card(conn, card_id)
    if not card:
        return None
    card["status_ar"] = STATUS_AR.get(card["status"], card["status"])
    card["ai_disclosure"] = "AI-assisted tool, not a fatwa authority."
    card["supported_means"] = (
        "Supported means the text was found in an approved source; "
        "it does not mean the surrounding claim or its application is correct."
    )
    return card


def card_page_payload(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "card_id": card["id"],
        "status": card["status"],
        "status_ar": STATUS_AR.get(card["status"], card["status"]),
        "matches": card["match_refs"],
        "diff": card.get("diff") or [],
        "diff_highlight": card.get("diff_highlight") or [],
        "user_diff_highlight": card.get("user_diff_highlight") or [],
        "correct_text": card.get("correct_text"),
        "matched_span": card.get("matched_span"),
        "gradings": card.get("gradings") or [],
        "score": card["score"],
        "card_url": f"/c/{card['id']}",
        "data_version": card["data_version"],
        "ai_disclosure": "AI-assisted tool, not a fatwa authority.",
        "supported_means": (
            "Supported means the text was found in an approved source; "
            "it does not mean the surrounding claim or its application is correct."
        ),
    }
