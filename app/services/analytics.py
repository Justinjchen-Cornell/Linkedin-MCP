from datetime import datetime, timedelta, timezone

from sqlalchemy import or_
from sqlmodel import Session, select

from app.models import AccountSnapshot, CapturedPost, PostMetric

SNAPSHOT_FIELDS = [
    "followers",
    "connections",
    "profile_views",
    "post_impressions_7d",
    "search_appearances_7d",
]


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _delta(latest: AccountSnapshot, previous: AccountSnapshot | None, field: str):
    if previous is None:
        return None
    current_value = getattr(latest, field, None)
    previous_value = getattr(previous, field, None)
    if current_value is None or previous_value is None:
        return None
    return current_value - previous_value


def _recent_metrics(session: Session, days: int) -> list[PostMetric]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    metrics = session.exec(
        select(PostMetric).order_by(PostMetric.captured_at.desc())
    ).all()
    return [metric for metric in metrics if (_aware(metric.captured_at) or since) >= since]


def _latest_by_urn(metrics: list[PostMetric]) -> dict[str, PostMetric]:
    latest: dict[str, PostMetric] = {}
    for metric in metrics:
        key = metric.urn or f"post:{metric.post_id}"
        if key not in latest:
            latest[key] = metric
    return latest


def overview(session: Session, days: int = 30) -> dict:
    recent = session.exec(
        select(AccountSnapshot).order_by(AccountSnapshot.captured_at.desc()).limit(10)
    ).all()
    def completeness(snapshot: AccountSnapshot) -> int:
        return sum(
            1 for field in SNAPSHOT_FIELDS if getattr(snapshot, field, None) is not None
        )
    recent.sort(
        key=lambda snapshot: (
            completeness(snapshot),
            _aware(snapshot.captured_at) or datetime.min.replace(tzinfo=timezone.utc),
        ),
        reverse=True,
    )
    snapshots = [item for item in recent if completeness(item) > 0]
    latest = snapshots[0] if snapshots else None
    previous = snapshots[1] if len(snapshots) > 1 else None
    deltas = {
        field: _delta(latest, previous, field) if latest else None
        for field in SNAPSHOT_FIELDS
    }

    latest_metrics = _latest_by_urn(_recent_metrics(session, days))
    impressions = sum(metric.impressions or 0 for metric in latest_metrics.values())
    engagements = sum(
        (metric.reactions or 0) + (metric.comments or 0) + (metric.reposts or 0)
        for metric in latest_metrics.values()
    )
    return {
        "latest": latest,
        "previous": previous,
        "deltas": deltas,
        "totals": {
            "impressions": impressions,
            "engagements": engagements,
            "posts": len(latest_metrics),
        },
        "latest_sync": recent[0].captured_at if recent else None,
    }


def latest_post_metrics(session: Session, days: int = 30, limit: int = 50) -> list[dict]:
    metrics = list(_latest_by_urn(_recent_metrics(session, days)).values())
    posts_by_urn = {
        post.urn: post
        for post in session.exec(select(CapturedPost)).all()
        if post.urn
    }
    items = []
    for metric in metrics:
        post = None
        if metric.urn:
            post = posts_by_urn.get(metric.urn)
        if post is None and metric.post_id:
            post = session.get(CapturedPost, metric.post_id)
        impressions = metric.impressions or 0
        engagement = (metric.reactions or 0) + (metric.comments or 0) + (metric.reposts or 0)
        items.append(
            {
                "id": metric.id,
                "urn": metric.urn,
                "post_id": metric.post_id or (post.id if post else None),
                "author_name": post.author_name if post else "",
                "text": post.text if post else "",
                "impressions": metric.impressions,
                "members_reached": metric.members_reached,
                "reactions": metric.reactions,
                "comments": metric.comments,
                "reposts": metric.reposts,
                "engagement_rate": engagement / impressions if impressions > 0 else None,
                "captured_at": metric.captured_at,
            }
        )
    items.sort(key=lambda item: item["impressions"] or 0, reverse=True)
    return items[:limit]


def best_times(session: Session) -> dict:
    from app.models import Schedule

    published = session.exec(
        select(Schedule).where(Schedule.status == "published", Schedule.published_at != None)  # noqa: E711
    ).all()
    counts: dict[tuple[int, int], int] = {}
    for item in published:
        moment = _aware(item.published_at)
        if moment is None:
            continue
        key = (moment.weekday(), moment.hour)
        counts[key] = counts.get(key, 0) + 1
    if len(published) >= 3 and counts:
        top = sorted(counts.items(), key=lambda pair: pair[1], reverse=True)[:3]
        return {
            "source": "history",
            "items": [{"weekday": weekday, "hour": hour, "count": count} for (weekday, hour), count in top],
        }
    return {
        "source": "default",
        "items": [
            {"weekday": 1, "hour": 9, "count": 0},
            {"weekday": 2, "hour": 9, "count": 0},
            {"weekday": 3, "hour": 9, "count": 0},
        ],
    }
