def test_account_snapshot_roundtrip(client):
    r = client.post("/api/extension/account-snapshot", json={
        "followers": 1773, "connections": 500, "profile_views": 965,
        "post_impressions_7d": 1512, "search_appearances_7d": 103,
        "raw_text": "1,773 followers ...",
    })
    assert r.status_code == 200
    items = client.get("/api/analytics/snapshots").json()["items"]
    assert items[0]["followers"] == 1773
    assert items[0]["connections"] == 500


def test_post_metrics_link_by_urn(client):
    client.post("/api/extension/capture", json={"posts": [{
        "urn": "urn:li:activity:999", "author_name": "Me", "text": "post",
        "impressions": 665,
    }]})
    r = client.post("/api/extension/post-metrics", json=[{
        "urn": "urn:li:activity:999", "impressions": 665, "members_reached": 184,
        "in_network_pct": 72, "out_network_pct": 28, "reactions": 0,
        "comments": 1, "reposts": 0,
    }])
    assert r.status_code == 200
    item = client.get("/api/analytics/post-metrics").json()["items"][0]
    assert item["urn"] == "urn:li:activity:999"
    assert item["members_reached"] == 184


def test_recapture_with_urn_updates_existing_post(client):
    base = {"posts": [{"author_name": "Me", "text": "same text"}]}
    client.post("/api/extension/capture", json=base)
    with_urn = {"posts": [{"urn": "urn:li:activity:555", "author_name": "Me", "text": "same text"}]}
    client.post("/api/extension/capture", json=with_urn)
    posts = client.get("/api/posts").json()["items"]
    assert len(posts) == 1
    assert posts[0]["urn"] == "urn:li:activity:555"


def test_overview_deltas_and_posts(client):
    client.post("/api/extension/account-snapshot", json={
        "captured_at": "2026-11-01T00:00:00Z", "followers": 100,
        "connections": 500, "profile_views": 900,
        "post_impressions_7d": 1000, "search_appearances_7d": 80,
    })
    client.post("/api/extension/account-snapshot", json={
        "captured_at": "2026-11-02T00:00:00Z", "followers": 110,
        "connections": 500, "profile_views": 965,
        "post_impressions_7d": 1512, "search_appearances_7d": 103,
    })
    client.post("/api/extension/capture", json={"posts": [{
        "urn": "urn:li:activity:1", "author_name": "Me", "text": "post one", "impressions": 665,
    }]})
    client.post("/api/extension/post-metrics", json=[{
        "urn": "urn:li:activity:1", "impressions": 665, "members_reached": 184,
        "reactions": 3, "comments": 2, "reposts": 1,
    }])
    data = client.get("/api/analytics/overview").json()
    assert data["latest"]["followers"] == 110
    assert data["deltas"]["followers"] == 10
    assert data["deltas"]["profile_views"] == 65
    posts = client.get("/api/analytics/posts").json()["items"]
    assert posts[0]["urn"] == "urn:li:activity:1"
    assert posts[0]["impressions"] == 665


def test_overview_ignores_empty_snapshot(client):
    client.post("/api/extension/account-snapshot", json={"followers": 100, "profile_views": 900})
    client.post("/api/extension/account-snapshot", json={})
    data = client.get("/api/analytics/overview").json()
    assert data["latest"]["followers"] == 100
    assert data["latest"]["profile_views"] == 900
