from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import CapturedPost, Comment
from app.services.heat import heat_score
from app.services.search import search_post_ids

router = APIRouter()


@router.get("/posts")
def list_posts(
    q: str = "",
    source: str | None = None,
    own: bool | None = None,
    min_reactions: int = 0,
    sort: str = "new",
    limit: int = 20,
    offset: int = 0,
    session: Session = Depends(get_session),
) -> dict:
    stmt = select(CapturedPost)
    if source:
        stmt = stmt.where(CapturedPost.source == source)
    if own is not None:
        stmt = stmt.where(CapturedPost.is_own == own)
    if min_reactions:
        stmt = stmt.where(CapturedPost.reactions >= min_reactions)
    if q:
        ids = search_post_ids(session, q)
        if not ids:
            return {"items": [], "total": 0}
        stmt = stmt.where(CapturedPost.id.in_(ids))

    posts = session.exec(stmt).all()
    total = len(posts)
    if sort == "heat":
        now = datetime.now(timezone.utc)
        posts.sort(key=lambda post: heat_score(post, now), reverse=True)
    else:
        posts.sort(
            key=lambda post: (post.posted_at or post.first_captured_at, post.id or 0),
            reverse=True,
        )
    page = posts[offset : offset + max(1, min(limit, 200))]
    return {"items": page, "total": total}


@router.get("/posts/{post_id}")
def get_post(post_id: int, session: Session = Depends(get_session)) -> dict:
    post = session.get(CapturedPost, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    comments = session.exec(
        select(Comment).where(Comment.post_id == post_id).order_by(Comment.id)
    ).all()
    data = post.model_dump()
    data["comments"] = [comment.model_dump() for comment in comments]
    return data
