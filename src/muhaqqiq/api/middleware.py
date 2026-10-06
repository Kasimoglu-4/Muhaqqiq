"""Abuse controls: rate limit, Turnstile, request ids (Phase 3.3)."""

from __future__ import annotations

import os
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable

import httpx
from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        request.state.request_id = rid
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-Id"] = rid
        request.state.latency_ms = (time.perf_counter() - started) * 1000
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple per-IP sliding window for public write endpoints."""

    def __init__(self, app, *, limit: int = 60, window_sec: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window = window_sec
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method in {"POST", "PUT", "PATCH"}:
            ip = request.client.host if request.client else "unknown"
            now = time.time()
            q = self._hits[ip]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.limit:
                return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
            q.append(now)
        return await call_next(request)


async def verify_turnstile(token: str | None, remote_ip: str | None = None) -> None:
    """Verify Cloudflare Turnstile when TURNSTILE_SECRET is set; otherwise no-op."""
    secret = os.environ.get("TURNSTILE_SECRET", "").strip()
    if not secret:
        return
    if not token:
        raise HTTPException(400, "Turnstile token required")
    data = {"secret": secret, "response": token}
    if remote_ip:
        data["remoteip"] = remote_ip
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post("https://challenges.cloudflare.com/turnstile/v0/siteverify", data=data)
        r.raise_for_status()
        body = r.json()
    if not body.get("success"):
        raise HTTPException(400, "Turnstile verification failed")
