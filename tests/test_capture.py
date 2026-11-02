from datetime import datetime, timezone


def payload(text="hello world", urn="urn:li:activity:1", comments=None):
    return {
        "page_url": "https://www.linkedin.com/feed/",
        "page_type": "feed",
        "posts": [{
            "urn": urn,
            "url": f"https://www.linkedin.com/feed/update/{urn}/",
            "author_name": "Alice",
            "author_url": "https://www.linkedin.com/in/alice/",
            "text": text,
            "posted_at": "2026-11-01T10:00:00Z",
            "reactions": 10,
            "comments_count": 2,
            "reposts": 1,
            "comments": comments or [],
        }],
    }


def test_capture_inserts_post_and_is_idempotent(client):
    r = client.post("/api/extension/capture", json=payload())
    assert r.status_code == 200
    assert r.json()["inserted"] == 1
    r2 = client.post("/api/extension/capture", json=payload())
    assert r2.json()["inserted"] == 0 and r2.json()["updated"] == 1
    assert len(client.get("/api/posts").json()["items"]) == 1


def test_capture_updates_higher_counts_and_comments(client):
    client.post("/api/extension/capture", json=payload())
    p = payload(text="hello world")
    p["posts"][0]["reactions"] = 99
    p["posts"][0]["comments"] = [{"author_name": "Bob", "author_url": "https://www.linkedin.com/in/bob/", "text": "nice"}]
    client.post("/api/extension/capture", json=p)
    detail = client.get("/api/posts/1").json()
    assert detail["reactions"] == 99
    assert detail["comments"][0]["author_name"] == "Bob"


def test_capture_rejects_too_many_posts(client):
    p = payload()
    p["posts"] = p["posts"] * 101
    assert client.post("/api/extension/capture", json=p).status_code == 422


def test_capture_sinks_authors_into_people(client):
    client.post("/api/extension/capture", json=payload())
    people = client.get("/api/people?q=Alice").json()
    assert people["total"] == 1
    assert people["items"][0]["url"] == "https://www.linkedin.com/in/alice/"


def test_capture_skips_post_without_text_or_author(client):
    p = payload()
    p["posts"] = [{"urn": "urn:empty"}]
    assert client.post("/api/extension/capture", json=p).json()["skipped"] == 1


def test_capture_dedups_by_url_when_urn_missing(client):
    p = payload(urn=None)
    p["posts"][0]["url"] = "https://www.linkedin.com/feed/update/abc/"
    client.post("/api/extension/capture", json=p)
    r = client.post("/api/extension/capture", json=p)
    assert r.json()["inserted"] == 0 and r.json()["updated"] == 1


def test_capture_truncates_raw_html(client):
    p = payload()
    p["posts"][0]["raw_html"] = "x" * 250_000
    client.post("/api/extension/capture", json=p)
    assert len(client.get("/api/posts/1").json()["raw_html"]) <= 200_000
