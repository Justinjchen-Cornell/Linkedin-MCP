def test_series_crud_and_defaults(client):
    r = client.post("/api/series", json={"name": "GOR Pulse", "slug": "gor-pulse", "weekday": 0, "template": "GOR template"})
    assert r.status_code == 201
    assert r.json()["next_number"] == 1
    assert client.patch(f"/api/series/{r.json()['id']}", json={"weekday": 2}).json()["weekday"] == 2
    assert client.delete(f"/api/series/{r.json()['id']}").status_code == 204
