from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models import AccountSnapshot, CapturedPost, PostMetric
from app.schemas.analytics import AccountSnapshotIn, PostMetricIn
from app.schemas.capture import CapturePayload
from app.services.capture import ingest_capture
from app.services.settings import get_setting, set_setting

router = APIRouter()


class PollRequest(BaseModel):
    extension_version: str = ""
    last_seen: str | None = None


@router.post("/extension/capture")
def capture(payload: CapturePayload, session: Session = Depends(get_session)) -> dict:
    result = ingest_capture(session, payload)
    return {
        "inserted": result.inserted,
        "updated": result.updated,
        "skipped": result.skipped,
        "post_ids": result.post_ids,
    }


@router.post("/extension/poll")
def poll(payload: PollRequest, session: Session = Depends(get_session)) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    set_setting(session, "extension_last_seen", now)
    session.commit()
    return {"tasks": [], "server_time": now}


@router.get("/extension/status")
def status(session: Session = Depends(get_session)) -> dict:
    last_seen = get_setting(session, "extension_last_seen") or None
    posts = session.exec(select(CapturedPost)).all()
    return {"last_seen": last_seen, "captured_posts": len(posts)}


@router.post("/extension/account-snapshot")
def ingest_account_snapshot(
    payload: AccountSnapshotIn, session: Session = Depends(get_session)
):
    data = payload.model_dump()
    captured_at = data.pop("captured_at") or datetime.now(timezone.utc)
    snapshot = AccountSnapshot(captured_at=captured_at, **data)
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot


@router.post("/extension/post-metrics")
def ingest_post_metrics(
    payload: list[PostMetricIn], session: Session = Depends(get_session)
) -> dict:
    inserted = 0
    for metric in payload:
        data = metric.model_dump()
        urn = data.pop("urn", None)
        captured_at = data.pop("captured_at") or datetime.now(timezone.utc)
        post_id = None
        if urn:
            post = session.exec(select(CapturedPost).where(CapturedPost.urn == urn)).first()
            if post:
                post_id = post.id
        session.add(
            PostMetric(
                post_id=post_id,
                urn=urn,
                captured_at=captured_at,
                **data,
            )
        )
        inserted += 1
    session.commit()
    return {"inserted": inserted}
