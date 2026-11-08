def test_draft_image_upload_and_serve(client):
    d = client.post("/api/drafts", json={"title": "T", "body": "B"}).json()
    files = {"file": ("test.png", b"fake-image-bytes", "image/png")}
    r = client.post(f"/api/drafts/{d['id']}/image", files=files)
    assert r.status_code == 200
    assert r.json()["image_path"]
    img = client.get(f"/api/drafts/{d['id']}/image")
    assert img.status_code == 200
    assert img.content == b"fake-image-bytes"


def test_best_times_returns_defaults(client):
    data = client.get("/api/analytics/best-times").json()
    assert len(data["items"]) >= 1
    assert data["source"] in {"default", "history"}
