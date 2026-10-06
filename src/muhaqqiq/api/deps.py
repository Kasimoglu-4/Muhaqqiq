"""Request helpers shared by routers."""

from __future__ import annotations

from fastapi import Request


def request_id(request: Request | None) -> str:
    if request is None:
        return "-"
    return getattr(request.state, "request_id", "-")
