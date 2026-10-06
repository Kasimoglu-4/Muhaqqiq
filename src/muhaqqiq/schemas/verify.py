"""Verify request models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class VerifyBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="Arabic text to verify")
    turnstile_token: str | None = Field(None, description="Cloudflare Turnstile token when enabled")
