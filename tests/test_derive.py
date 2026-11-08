def test_derive_creates_two_light_drafts(client):
    d = client.post("/api/drafts", json={"title": "Deep", "body": "VIX closed 21.15. Credit spreads are widening.\n\nMy view: this is a liquidity story."}).json()
    items = client.post(f"/api/drafts/{d['id']}/derive").json()["items"]
    assert len(items) == 2
    assert all(x["kind"] == "light" and x["parent_draft_id"] == d["id"] for x in items)
    assert "21.15" in items[0]["body"]
