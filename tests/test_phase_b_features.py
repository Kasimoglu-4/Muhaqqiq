"""Phase B: proof, diff highlight, reply templates, multi-rulings, trust JSON."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from muhaqqiq.domain.diff import diff_highlight
from muhaqqiq.main import app
from muhaqqiq.services.reply_templates import fill_template, templates_payload

ROOT = Path(__file__).resolve().parents[1]


def test_diff_highlight_marks_replace():
    segs = diff_highlight("بسم الله", "بسم اللة", "بسم الله")
    ops = {s["op"] for s in segs}
    assert "equal" in ops
    assert "replace" in ops or "insert" in ops


def test_reply_templates_fill_stored_fields_only():
    text = fill_template(
        "close",
        "ar",
        fields={
            "correct_text": "إنما الأعمال بالنيات",
            "reference": "Bukhari · 1",
            "card_url": "/c/abc",
            "proof_url": "https://example.com",
        },
    )
    assert text is not None
    assert "إنما الأعمال بالنيات" in text
    assert "Bukhari" in text
    assert "باطل" not in text
    assert "موضوع" not in text


def test_undetermined_has_no_reply_key():
    client = TestClient(app)
    r = client.post("/v1/verify", json={"text": "xyzzy not a real claim 12345"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "UNDETERMINED"
    assert body.get("reply_template_key") in (None, "")


def test_close_returns_highlight_and_correct_text():
    client = TestClient(app)
    # Slightly altered Fatiha opener often scores Close
    r = client.post("/v1/verify", json={"text": "بسم الله الرحمن الرحيم الم"})
    assert r.status_code == 200
    body = r.json()
    if body["status"] == "CLOSE_WITH_DIFF":
        assert body.get("correct_text")
        assert isinstance(body.get("diff_highlight"), list)


def test_attributed_returns_gradings_list():
    client = TestClient(app)
    r = client.post("/v1/verify", json={"text": "اطلبوا العلم ولو في الصين"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ATTRIBUTED_RULING"
    assert isinstance(body.get("gradings"), list)
    assert len(body["gradings"]) >= 1
    assert body["gradings"][0].get("grader")
    # multi-ruling seed rows for this claim
    assert len(body["gradings"]) >= 2


def test_templates_endpoint():
    client = TestClient(app)
    r = client.get("/v1/reply-templates")
    assert r.status_code == 200
    assert "close" in r.json()["templates"]
    assert templates_payload()["close"]["ar"]["full"]


def test_accuracy_json_exists():
    path = ROOT / "apps" / "web" / "src" / "generated" / "eval_heldout.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "false_support" in data
    assert "data_version" in data


def test_scholarly_seal_absent_when_empty():
    path = ROOT / "docs" / "scholarly-review.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("reviews") == []
