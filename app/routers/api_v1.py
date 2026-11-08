import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.db import get_session
from app.models import CapturedPost, Comment, PostMetric
from app.routers.people import list_people
from app.routers.posts import get_post, list_posts
from app.services.analytics import latest_post_metrics
from app.services.analytics import overview as analytics_overview
from app.services.settings import get_setting

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "api": "v1"}


@router.get("/me")
def me(session: Session = Depends(get_session)) -> dict:
    data = analytics_overview(session)
    latest = data["latest"]
    posts = session.exec(select(CapturedPost)).all()
    return {
        "profile_url": get_setting(session, "own_profile_url", ""),
        "followers": getattr(latest, "followers", None),
        "connections": getattr(latest, "connections", None),
        "profile_views": getattr(latest, "profile_views", None),
        "post_impressions_7d": getattr(latest, "post_impressions_7d", None),
        "search_appearances_7d": getattr(latest, "search_appearances_7d", None),
        "posts": len(posts),
        "latest_sync": getattr(latest, "captured_at", None),
    }


@router.get("/posts")
def posts(
    q: str = "",
    source: str | None = None,
    own: bool | None = None,
    min_reactions: int = 0,
    sort: str = "new",
    limit: int = 20,
    offset: int = 0,
    session: Session = Depends(get_session),
) -> dict:
    return list_posts(
        q=q,
        source=source,
        own=own,
        min_reactions=min_reactions,
        sort=sort,
        limit=limit,
        offset=offset,
        session=session,
    )


@router.get("/posts/{post_id}")
def post_detail(post_id: int, session: Session = Depends(get_session)) -> dict:
    return get_post(post_id, session)


@router.get("/posts/{post_id}/metrics")
def post_metrics(post_id: int, session: Session = Depends(get_session)) -> dict:
    post = session.get(CapturedPost, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    metrics = session.exec(
        select(PostMetric)
        .where(PostMetric.post_id == post_id)
        .order_by(PostMetric.captured_at.desc())
    ).all()
    if not metrics and post.urn:
        metrics = session.exec(
            select(PostMetric)
            .where(PostMetric.urn == post.urn)
            .order_by(PostMetric.captured_at.desc())
        ).all()
    return metrics[0].model_dump() if metrics else {}


@router.get("/people")
def people(
    q: str = "",
    limit: int = 20,
    offset: int = 0,
    session: Session = Depends(get_session),
) -> dict:
    return list_people(q=q, limit=limit, offset=offset, session=session)


@router.get("/comments")
def comments(
    post_id: int | None = None,
    limit: int = 50,
    session: Session = Depends(get_session),
) -> dict:
    stmt = select(Comment)
    if post_id is not None:
        stmt = stmt.where(Comment.post_id == post_id)
    items = session.exec(stmt.order_by(Comment.id.desc()).limit(limit)).all()
    return {"items": items, "total": len(items)}


@router.get("/analytics/overview")
def analytics(days: int = 30, session: Session = Depends(get_session)) -> dict:
    return analytics_overview(session, days)


@router.get("/analytics/posts")
def analytics_posts(
    days: int = 30, limit: int = 50, session: Session = Depends(get_session)
) -> dict:
    items = latest_post_metrics(session, days, limit)
    return {"items": items, "total": len(items)}


@router.get("/search")
def search(
    q: str,
    limit: int = 20,
    offset: int = 0,
    session: Session = Depends(get_session),
) -> dict:
    return list_posts(
        q=q,
        source=None,
        own=None,
        min_reactions=0,
        sort="new",
        limit=limit,
        offset=offset,
        session=session,
    )


@router.get("/export")
def export(format: str = "json", session: Session = Depends(get_session)):
    posts = session.exec(select(CapturedPost).order_by(CapturedPost.id)).all()
    if format == "json":
        return {"items": [post.model_dump() for post in posts]}
    if format != "csv":
        raise HTTPException(status_code=400, detail="format must be json or csv")

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "urn",
            "author_name",
            "text",
            "reactions",
            "comments_count",
            "reposts",
            "posted_at",
            "url",
            "source",
        ]
    )
    for post in posts:
        writer.writerow(
            [
                post.id,
                post.urn,
                post.author_name,
                post.text,
                post.reactions,
                post.comments_count,
                post.reposts,
                post.posted_at,
                post.url,
                post.source,
            ]
        )
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=linkedin-posts.csv"},
    )
