from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import CapturedPost, Comment

router = APIRouter()


@router.get("/posts")
def list_posts(session: Session = Depends(get_session)) -> dict:
    posts = session.exec(select(CapturedPost).order_by(CapturedPost.id.desc())).all()
    return {"items": posts, "total": len(posts)}


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
