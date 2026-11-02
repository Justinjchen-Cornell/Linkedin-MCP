from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models import CapturedPost
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
