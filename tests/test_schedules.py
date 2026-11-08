def test_schedule_due_and_published(client):
    d = client.post("/api/drafts", json={"title": "T", "body": "post"}).json()
    r = client.post(f"/api/drafts/{d['id']}/schedule", json={"scheduled_at": "2026-11-01T00:00:00Z", "timezone": "Asia/Shanghai"})
    assert r.status_code == 201
    sid = r.json()["id"]
    due = client.get("/api/schedules/due").json()["items"]
    assert due[0]["id"] == sid
    assert client.post(f"/api/schedules/{sid}/published", json={"published_url": "https://x"}).status_code == 200
    assert client.get("/api/schedules/due").json()["items"] == []


def test_schedule_opened_and_notified(client):
    d = client.post("/api/drafts", json={"title": "T", "body": "post"}).json()
    sid = client.post(f"/api/drafts/{d['id']}/schedule", json={"scheduled_at": "2026-11-01T00:00:00Z"}).json()["id"]
    assert client.post(f"/api/schedules/{sid}/opened").status_code == 200
    assert client.post(f"/api/schedules/{sid}/notified").status_code == 200
    row = client.get("/api/schedules").json()["items"][0]
    assert row["opened_at"] is not None and row["notified_at"] is not None


def test_due_excludes_published_but_includes_notified_until_published(client):
    d = client.post("/api/drafts", json={"title": "T", "body": "post"}).json()
    sid = client.post(f"/api/drafts/{d['id']}/schedule", json={"scheduled_at": "2026-11-01T00:00:00Z"}).json()["id"]
    client.post(f"/api/schedules/{sid}/notified")
    assert client.get("/api/schedules/due").json()["items"][0]["id"] == sid
    client.post(f"/api/schedules/{sid}/published", json={})
    assert client.get("/api/schedules/due").json()["items"] == []


def test_schedule_detail_includes_draft_body(client):
    d = client.post("/api/drafts", json={"title": "T", "body": "detail body"}).json()
    sid = client.post(f"/api/drafts/{d['id']}/schedule", json={"scheduled_at": "2026-11-01T00:00:00Z"}).json()["id"]
    data = client.get(f"/api/schedules/{sid}").json()
    assert data["draft_body"] == "detail body"
