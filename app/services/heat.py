from datetime import datetime, timezone

from app.models import CapturedPost


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def heat_score(post: CapturedPost, now: datetime) -> float:
    anchor = _aware(post.posted_at or post.first_captured_at)
    age_hours = max((_aware(now) - anchor).total_seconds() / 3600, 1.0)
    return (post.reactions + 2 * post.comments_count + 3 * post.reposts) / age_hours
