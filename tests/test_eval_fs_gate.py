"""CI-facing gate: holdout false-support must stay 0."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_heldout_json_fs_zero_when_present():
    path = ROOT / "apps" / "web" / "src" / "generated" / "eval_heldout.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not data.get("n"):
        return
    assert data["false_support"] == 0
    seal = data.get("technical_seal")
    if seal:
        assert seal.get("false_support") == 0
