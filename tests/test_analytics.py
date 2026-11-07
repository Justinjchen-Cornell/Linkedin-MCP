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
