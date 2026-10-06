"""Status labels and reply-template keys (no I/O)."""

from __future__ import annotations

STATUS_AR = {
    "SUPPORTED": "مؤيَّد بمصدر",
    "CLOSE_WITH_DIFF": "قريب مع اختلاف",
    "ATTRIBUTED_RULING": "حكم منسوب",
    "UNDETERMINED": "لم يُحسم",
}

REPLY_TEMPLATE_KEYS = {
    "CLOSE_WITH_DIFF": "close",
    "ATTRIBUTED_RULING": "attributed",
    "SUPPORTED": "supported_copy",
}
