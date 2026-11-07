from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import AccountSnapshot, PostMetric

router = APIRouter()


@router.get("/analytics/snapshots")
def list_snapshots(limit: int = 10, session: Session = Depends(get_session)) -> dict:
    items = session.exec(
        select(AccountSnapshot).order_by(AccountSnapshot.captured_at.desc()).limit(limit)
    ).all()
    return {"items": items}


@router.get("/analytics/post-metrics")
def list_post_metrics(limit: int = 20, session: Session = Depends(get_session)) -> dict:
    items = session.exec(
        select(PostMetric).order_by(PostMetric.captured_at.desc()).limit(limit)
    ).all()
    return {"items": items}
