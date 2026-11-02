def test_poll_returns_empty_tasks_and_updates_status(client):
    r = client.post("/api/extension/poll", json={"extension_version": "0.1.0", "last_seen": None})
    assert r.status_code == 200
    assert r.json()["tasks"] == []
    status = client.get("/api/extension/status").json()
    assert status["last_seen"] is not None
    assert status["captured_posts"] == 0
