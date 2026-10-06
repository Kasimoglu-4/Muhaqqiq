from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from muhaqqiq.main import app


def test_health():
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["ok"] is True


def test_verify_text():
    with TestClient(app) as client:
        r = client.post("/v1/verify", json={"text": "إنما الأعمال بالنيات"})
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "SUPPORTED"
        assert "card_id" in body
        assert "X-Request-Id" in r.headers


def test_verify_multipart_text():
    with TestClient(app) as client:
        r = client.post("/v1/verify", data={"text": "إنما الأعمال بالنيات"})
        assert r.status_code == 200
        assert r.json()["status"] == "SUPPORTED"


def test_verify_image_returns_editable_text():
    buf = BytesIO()
    Image.new("RGB", (32, 32), (255, 255, 255)).save(buf, format="PNG")
    with TestClient(app) as client:
        r = client.post(
            "/v1/verify",
            files={"image": ("t.png", buf.getvalue(), "image/png")},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["editable"] is True
        assert "extracted_text" in body


def test_card_persists_diff():
    with TestClient(app) as client:
        # slightly altered known verse often yields CLOSE_WITH_DIFF or UNDETERMINED
        r = client.post("/v1/verify", json={"text": "الحمد لله رب العالمين الرحمن"})
        assert r.status_code == 200
        cid = r.json()["card_id"]
        diff = r.json().get("diff") or []
        card = client.get(f"/v1/cards/{cid}")
        assert card.status_code == 200
        assert card.json().get("diff") == diff


def test_feedback():
    with TestClient(app) as client:
        r = client.post("/v1/feedback", json={"kind": "useful", "comment": "ok"})
        assert r.status_code == 200
        assert r.json()["ok"] == "true"


def test_sources():
    with TestClient(app) as client:
        r = client.get("/v1/sources")
        assert r.status_code == 200
        assert "sources" in r.json()


def test_og_png():
    with TestClient(app) as client:
        r = client.post("/v1/verify", json={"text": "إنما الأعمال بالنيات"})
        cid = r.json()["card_id"]
        png = client.get(f"/c/{cid}/og.png")
        assert png.status_code == 200
        assert png.headers["content-type"] == "image/png"
        assert png.content[:8] == b"\x89PNG\r\n\x1a\n"
