from fastapi.testclient import TestClient

from muhaqqiq.main import app


def test_ops_summary_and_health_ops():
    with TestClient(app) as client:
        client.post("/v1/verify", json={"text": "إنما الأعمال بالنيات"})
        r = client.get("/v1/ops/summary")
        assert r.status_code == 200
        body = r.json()
        assert body["verify_total"] >= 1
        assert "SUPPORTED" in body["status_counts"]
        h = client.get("/health")
        assert "ops" in h.json()
