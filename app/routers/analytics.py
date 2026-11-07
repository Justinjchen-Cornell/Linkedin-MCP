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


@router.get("/analytics/overview")
def analytics_overview(days: int = 30, session: Session = Depends(get_session)) -> dict:
    from app.services.analytics import overview

    return overview(session, days)


@router.get("/analytics/posts")
def analytics_posts(
    days: int = 30,
    limit: int = 50,
    session: Session = Depends(get_session),
) -> dict:
    from app.services.analytics import latest_post_metrics

    items = latest_post_metrics(session, days, limit)
    return {"items": items, "total": len(items)}
