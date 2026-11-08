def test_sync_fetch_times_out_with_status(client):
    client.put("/api/settings", json={"own_profile_url": "https://www.linkedin.com/in/me/"})
    r = client.post("/api/v1/fetch", json={"type": "profile", "sync": True, "timeout": 2})
    assert r.status_code in {200, 202}
    data = r.json()
    assert data["status"] in {"queued", "running"}
    assert data["id"] >= 1


def test_sync_fetch_returns_result_when_worker_completes(client):
    import threading
    import time
    from fastapi.testclient import TestClient
    from app.main import app

    client.put("/api/settings", json={"own_profile_url": "https://www.linkedin.com/in/me/"})

    def worker():
        time.sleep(0.5)
        other = TestClient(app)
        job = other.get("/api/extension/jobs/next").json()["job"]
        other.post(f"/api/extension/jobs/{job['id']}/result", json={
            "ok": True,
            "result": {
                "ok": True,
                "snapshot": {"followers": 1775},
                "posts": [{"urn": "urn:li:activity:1", "author_name": "Me", "text": "live"}],
                "page_url": "https://www.linkedin.com/in/me/",
            },
        })

    threading.Thread(target=worker).start()
    r = client.post("/api/v1/fetch", json={"type": "profile", "sync": True, "timeout": 10})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "done"
    assert data["result"]["snapshot"]["followers"] == 1775
