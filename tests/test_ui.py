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


def test_settings_page_saves_profile_and_watchlist(client):
    r = client.post("/settings", data={"own_profile_url": "https://www.linkedin.com/in/me/",
                                       "capture_scroll_screens": "3",
                                       "max_posts_per_capture": "100"}, follow_redirects=False)
    assert r.status_code == 303
    assert client.get("/api/settings").json()["own_profile_url"] == "https://www.linkedin.com/in/me/"
    r2 = client.post("/watchlist", data={"kind": "keyword", "value": "SaaS"}, follow_redirects=False)
    assert r2.status_code == 303
    assert len(client.get("/api/watchlist").json()) == 1


def test_analytics_page_shows_snapshot_and_posts(client):
    client.post("/api/extension/account-snapshot", json={"followers": 1773, "profile_views": 965})
    client.post("/api/extension/capture", json={"posts": [{"urn": "urn:1", "author_name": "Me", "text": "post", "impressions": 665}]})
    client.post("/api/extension/post-metrics", json=[{"urn": "urn:1", "impressions": 665}])
    html = client.get("/analytics").text
    assert "1,773" in html and "665" in html


def test_settings_saves_analytics_sync_hour(client):
    r = client.post("/settings", data={"own_profile_url": "", "capture_scroll_screens": "3",
                                       "max_posts_per_capture": "100", "analytics_sync_hour": "9"},
                    follow_redirects=False)
    assert r.status_code == 303
    assert client.get("/api/settings").json()["analytics_sync_hour"] == "9"
