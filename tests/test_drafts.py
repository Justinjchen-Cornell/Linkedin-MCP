def test_draft_crud_and_3000_limit(client):
    r = client.post("/api/drafts", json={"title": "T", "body": "hello"})
    assert r.status_code == 201
    draft_id = r.json()["id"]
    assert client.patch(f"/api/drafts/{draft_id}", json={"body": "hi"}).json()["body"] == "hi"
    assert client.post("/api/drafts", json={"body": "x" * 3001}).status_code == 422
    assert client.delete(f"/api/drafts/{draft_id}").status_code == 204
