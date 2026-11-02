def test_posts_page_lists_and_filters(client):
    payload = {"page_url": "https://www.linkedin.com/feed/", "page_type": "feed", "posts": [
        {"urn": "urn:1", "author_name": "Alice", "text": "AI content ops", "reactions": 10},
        {"urn": "urn:2", "author_name": "Bob", "text": "LinkedIn growth", "reactions": 1},
    ]}
    client.post("/api/extension/capture", json=payload)
    html = client.get("/posts").text
    assert "Alice" in html and "AI content ops" in html
    filtered = client.get("/posts?q=LinkedIn").text
    assert "Bob" in filtered and "Alice" not in filtered


def test_post_detail_shows_comments(client):
    payload = {"page_url": "https://www.linkedin.com/feed/", "page_type": "feed", "posts": [
        {"urn": "urn:1", "author_name": "Alice", "text": "hello", "comments": [{"author_name": "Bob", "text": "nice"}]}
    ]}
    client.post("/api/extension/capture", json=payload)
    html = client.get("/posts/1").text
    assert "hello" in html and "nice" in html
