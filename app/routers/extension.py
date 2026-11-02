from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.schemas.capture import CapturePayload
from app.services.capture import ingest_capture

router = APIRouter()


@router.post("/extension/capture")
def capture(payload: CapturePayload, session: Session = Depends(get_session)) -> dict:
    result = ingest_capture(session, payload)
    return {
        "inserted": result.inserted,
        "updated": result.updated,
        "skipped": result.skipped,
        "post_ids": result.post_ids,
    }
