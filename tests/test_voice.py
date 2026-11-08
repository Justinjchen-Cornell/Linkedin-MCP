def test_voice_roundtrip(client):
    r = client.put("/api/voice", json={"beliefs": "Liquidity first", "banned_phrases": "delve, game-changer"})
    assert r.status_code == 200
    data = client.get("/api/voice").json()
    assert data["beliefs"] == "Liquidity first"
    assert data["banned_phrases"] == "delve, game-changer"


def test_ai_prompt_includes_voice(client, monkeypatch):
    client.put("/api/voice", json={"beliefs": "Liquidity first"})
    monkeypatch.setattr("app.services.ai_config.get_api_key", lambda: "test-key")
    captured = {}

    def fake_chat(messages, base_url, model, api_key):
        captured["messages"] = messages
        return '{"variants":[]}'

    monkeypatch.setattr("app.services.ai._chat", fake_chat)
    client.post("/api/ai/generate", json={"topic": "AI capex"})
    assert "Liquidity first" in str(captured["messages"])
