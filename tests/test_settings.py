def test_settings_roundtrip(client):
    r = client.put("/api/settings", json={"own_profile_url": "https://www.linkedin.com/in/test/"})
    assert r.status_code == 200
    assert client.get("/api/settings").json()["own_profile_url"] == "https://www.linkedin.com/in/test/"


def test_settings_put_is_partial(client):
    client.put("/api/settings", json={"a": "1", "b": "2"})
    client.put("/api/settings", json={"b": "3"})
    assert client.get("/api/settings").json() == {"a": "1", "b": "3"}
