def test_next_issue_increments(client):
    s = client.post("/api/series", json={"name": "GOR", "slug": "gor", "weekday": 0, "template": "T"}).json()
    d1 = client.post(f"/api/series/{s['id']}/next-issue").json()
    d2 = client.post(f"/api/series/{s['id']}/next-issue").json()
    assert d1["issue_number"] == 1 and d2["issue_number"] == 2
    assert client.get("/api/series").json()[0]["next_number"] == 3


def test_week_plan_has_five_slots(client):
    client.post("/api/series", json={"name": "GOR", "slug": "gor", "weekday": 0, "template": "T"})
    plan = client.get("/api/plan/week").json()
    assert len(plan["slots"]) == 5
    assert plan["slots"][0]["kind"] == "deep"
    assert plan["slots"][0]["series_name"] == "GOR"
    assert plan["slots"][2]["kind"] == "light"


def test_plan_shows_created_next_issue(client):
    s = client.post("/api/series", json={"name": "GOR", "slug": "gor2", "weekday": 0, "template": "T"}).json()
    d = client.post(f"/api/series/{s['id']}/next-issue").json()
    plan = client.get("/api/plan/week").json()
    assert plan["slots"][0]["draft_id"] == d["id"]
    assert plan["slots"][0]["issue_number"] == 1
