def test_health_returns_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "version": "0.1.0"}


def test_rejects_cross_origin_writes(client):
    r = client.post("/api/anything", headers={"Origin": "https://evil.com"})
    assert r.status_code == 403
