def test_v1_posts_me_and_export(client):
    client.put("/api/settings", json={"own_profile_url": "https://www.linkedin.com/in/me/"})
    client.post("/api/extension/capture", json={"posts": [{
        "urn": "urn:li:activity:1", "author_name": "Me", "text": "hello api",
        "reactions": 3, "comments_count": 1,
        "comments": [{"author_name": "Bob", "text": "nice"}],
    }]})
    client.post("/api/extension/account-snapshot", json={"followers": 1773, "profile_views": 965})
    client.post("/api/extension/post-metrics", json=[{"urn": "urn:li:activity:1", "impressions": 665, "members_reached": 184}])

    posts = client.get("/api/v1/posts").json()
    assert posts["total"] == 1
    assert posts["items"][0]["text"] == "hello api"

    me = client.get("/api/v1/me").json()
    assert me["followers"] == 1773
    assert me["posts"] == 1

    detail = client.get("/api/v1/posts/1").json()
    assert detail["comments"][0]["author_name"] == "Bob"

    metrics = client.get("/api/v1/posts/1/metrics").json()
    assert metrics["impressions"] == 665

    csv = client.get("/api/v1/export?format=csv")
    assert csv.status_code == 200 and "hello api" in csv.text
