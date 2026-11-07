def test_ai_without_key_returns_400(client, monkeypatch):
    monkeypatch.setattr("app.services.ai_config.get_api_key", lambda: "")
    r = client.post("/api/ai/generate", json={"topic": "AI capex"})
    assert r.status_code == 400


def test_style_profile_uses_own_posts(client):
    client.put("/api/settings", json={"own_profile_url": "https://www.linkedin.com/in/me/"})
    client.post("/api/extension/capture", json={"posts": [{
        "author_name": "Me", "author_url": "https://www.linkedin.com/in/me/",
        "text": "Hello LinkedIn. #AI #Macro", "reactions": 1,
    }]})
    profile = client.get("/api/ai/style-profile").json()
    assert profile["sample_count"] == 1
    assert "Hello LinkedIn" in profile["samples"][0]


def test_generate_with_mock_provider(client, monkeypatch):
    monkeypatch.setattr("app.services.ai_config.get_api_key", lambda: "test-key")
    monkeypatch.setattr(
        "app.services.ai._chat",
        lambda messages, base_url, model, api_key: '{"variants":[{"title":"T","body":"B","hook_type":"question","rationale":"R"}]}',
    )
    r = client.post("/api/ai/generate", json={"topic": "AI capex", "count": 1})
    assert r.status_code == 200
    assert r.json()["variants"][0]["body"] == "B"
