def test_own_flag_and_filter(client):
    client.put("/api/settings", json={"own_profile_url": "https://www.linkedin.com/in/me/"})
    payload = {"page_url": "https://www.linkedin.com/in/me/recent-activity/all/", "page_type": "profile", "posts": [
        {"urn": "urn:me:1", "author_name": "Me", "author_url": "https://www.linkedin.com/in/me/", "text": "my post", "reactions": 5},
        {"urn": "urn:other:1", "author_name": "Other", "author_url": "https://www.linkedin.com/in/other/", "text": "other post", "reactions": 1},
    ]}
    client.post("/api/extension/capture", json=payload)
    assert client.get("/api/posts?own=true").json()["total"] == 1
    assert client.get("/api/posts?own=true").json()["items"][0]["text"] == "my post"
