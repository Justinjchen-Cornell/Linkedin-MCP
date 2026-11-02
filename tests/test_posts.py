def test_posts_filter_search_and_sort(client):
    base = {"page_url": "https://www.linkedin.com/feed/", "page_type": "feed", "posts": [
        {"urn": "urn:1", "author_name": "Alice", "text": "AI 内容运营", "reactions": 1, "comments_count": 0, "reposts": 0},
        {"urn": "urn:2", "author_name": "Bob", "text": "LinkedIn growth", "reactions": 50, "comments_count": 5, "reposts": 2},
    ]}
    client.post("/api/extension/capture", json=base)
    assert client.get("/api/posts?q=运营").json()["total"] == 1
    assert client.get("/api/posts?q=LinkedIn").json()["items"][0]["author_name"] == "Bob"
    assert client.get("/api/posts?min_reactions=10").json()["total"] == 1
    assert client.get("/api/posts?sort=heat").json()["items"][0]["author_name"] == "Bob"
