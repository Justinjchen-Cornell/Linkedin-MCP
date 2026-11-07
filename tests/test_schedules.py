def test_schedule_due_and_published(client):
    d = client.post("/api/drafts", json={"title": "T", "body": "post"}).json()
    r = client.post(f"/api/drafts/{d['id']}/schedule", json={"scheduled_at": "2026-11-01T00:00:00Z", "timezone": "Asia/Shanghai"})
    assert r.status_code == 201
    sid = r.json()["id"]
    due = client.get("/api/schedules/due").json()["items"]
    assert due[0]["id"] == sid
    assert client.post(f"/api/schedules/{sid}/published", json={"published_url": "https://x"}).status_code == 200
    assert client.get("/api/schedules/due").json()["items"] == []
