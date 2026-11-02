def test_watchlist_crud_and_round(client):
    r = client.post("/api/watchlist", json={"kind": "keyword", "value": "SaaS"})
    assert r.status_code == 201
    item_id = r.json()["id"]
    assert len(client.get("/api/watchlist").json()) == 1
    task = client.get("/api/watchlist/round?limit=5").json()["tasks"][0]
    assert task["id"] == item_id and "keywords=SaaS" in task["url"]
    assert client.delete(f"/api/watchlist/{item_id}").status_code == 204
    assert client.get("/api/watchlist").json() == []


def test_watchlist_duplicate_returns_409(client):
    client.post("/api/watchlist", json={"kind": "keyword", "value": "SaaS"})
    assert client.post("/api/watchlist", json={"kind": "keyword", "value": "SaaS"}).status_code == 409


def test_round_limits_to_five(client):
    for i in range(7):
        client.post("/api/watchlist", json={"kind": "keyword", "value": f"k{i}"})
    assert len(client.get("/api/watchlist/round?limit=5").json()["tasks"]) == 5
