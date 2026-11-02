import json
from pathlib import Path


def test_extension_payload_contract_is_accepted(client):
    payload = json.loads(Path("tests/fixtures/capture_payload.json").read_text(encoding="utf-8"))
    r = client.post("/api/extension/capture", json=payload)
    assert r.status_code == 200
    assert r.json()["inserted"] == 2
