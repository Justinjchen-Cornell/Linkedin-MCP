def test_profile_fetch_job(client):
    client.put("/api/settings", json={"own_profile_url": "https://www.linkedin.com/in/me/"})
    r = client.post("/api/v1/fetch", json={"type": "profile"})
    assert r.status_code == 202, r.text
    assert "id" in r.json(), r.json()
    job_id = r.json()["id"]
    job = client.get("/api/extension/jobs/next").json()["job"]
    assert job["id"] == job_id and job["status"] == "running"
    result = {"ok": True, "result": {
        "ok": True,
        "snapshot": {"followers": 1775, "profile_views": 953},
        "posts": [{"urn": "urn:li:activity:1", "author_name": "Me", "text": "hello"}],
        "page_url": "https://www.linkedin.com/in/me/",
    }}
    assert client.post(f"/api/extension/jobs/{job_id}/result", json=result).status_code == 200
    assert client.get(f"/api/v1/jobs/{job_id}").json()["status"] == "done"
    assert client.get("/api/v1/me").json()["followers"] == 1775
    assert client.get("/api/v1/posts").json()["total"] == 1


def test_post_metrics_fetch_job(client):
    client.post("/api/extension/capture", json={"posts": [{
        "urn": "urn:li:activity:1", "author_name": "Me", "text": "post",
    }]})
    job = client.post("/api/v1/fetch", json={
        "type": "post_metrics",
        "url": "https://www.linkedin.com/analytics/post-summary/urn:li:activity:1/",
    }).json()
    assert client.get("/api/extension/jobs/next").json()["job"]["id"] == job["id"]
    result = {"ok": True, "result": {"ok": True, "metrics": {
        "urn": "urn:li:activity:1", "impressions": 665, "members_reached": 184,
    }}}
    client.post(f"/api/extension/jobs/{job['id']}/result", json=result)
    metrics = client.get("/api/v1/posts/1/metrics").json()
    assert metrics["impressions"] == 665


def test_fetch_post_and_batch(client):
    client.post("/api/extension/capture", json={"posts": [
        {"urn": "urn:li:activity:1", "author_name": "Me", "text": "one"},
        {"urn": "urn:li:activity:2", "author_name": "Me", "text": "two"},
    ]})
    single = client.post("/api/v1/posts/1/fetch")
    assert single.status_code == 202 and single.json()["type"] == "post_metrics"
    batch = client.post("/api/v1/fetch", json={"type": "all_post_metrics", "limit": 2})
    assert batch.status_code == 202 and len(batch.json()["jobs"]) == 2
