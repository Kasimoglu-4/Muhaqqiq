"""Optional Sentry + in-process ops metrics (Phase 6.1)."""

from __future__ import annotations

import os
import threading
import time
from collections import Counter, deque

_lock = threading.Lock()
_status_counts: Counter[str] = Counter()
_latencies_ms: deque[float] = deque(maxlen=500)
_started = time.time()


def init_sentry() -> bool:
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        return False
    try:
        import sentry_sdk
    except ImportError:
        return False
    sentry_sdk.init(dsn=dsn, traces_sample_rate=0.05, send_default_pii=False)
    return True


def record_verify(status: str, latency_ms: float) -> None:
    with _lock:
        _status_counts[status] += 1
        _latencies_ms.append(latency_ms)


def ops_summary(*, ocr_spend: dict | None = None) -> dict:
    with _lock:
        lats = sorted(_latencies_ms)
        n = len(lats)
        p50 = lats[n // 2] if n else 0.0
        p95 = lats[max(0, int(n * 0.95) - 1)] if n else 0.0
        statuses = dict(_status_counts)
        verify_total = sum(_status_counts.values())
    return {
        "uptime_sec": round(time.time() - _started, 1),
        "verify_total": verify_total,
        "status_counts": statuses,
        "latency_p50_ms": round(p50, 1),
        "latency_p95_ms": round(p95, 1),
        "latency_samples": n,
        "ocr": ocr_spend or {},
    }
