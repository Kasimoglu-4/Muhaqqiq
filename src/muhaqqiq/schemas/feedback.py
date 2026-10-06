"""Feedback request models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class FeedbackBody(BaseModel):
    card_id: str | None = None
    kind: Literal["useful", "wrong", "other"] = "useful"
    comment: str = Field("", max_length=500)
    turnstile_token: str | None = None
