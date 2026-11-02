from datetime import datetime, timedelta, timezone

from app.models import CapturedPost
from app.services.heat import heat_score


def test_heat_score_uses_age_and_weighted_engagement():
    now = datetime(2026, 11, 3, 12, tzinfo=timezone.utc)
    post = CapturedPost(
        author_name="A",
        text="x",
        posted_at=now - timedelta(hours=2),
        reactions=10,
        comments_count=5,
        reposts=1,
        content_hash="h",
        first_captured_at=now,
        last_captured_at=now,
    )
    assert heat_score(post, now) == (10 + 2 * 5 + 3 * 1) / 2
