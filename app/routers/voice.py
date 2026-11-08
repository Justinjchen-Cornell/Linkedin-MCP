from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.schemas.voice import VoiceGuideIn, VoiceGuideRead
from app.services.voice import get_voice_guide

router = APIRouter()


@router.get("/voice", response_model=VoiceGuideRead)
def read_voice(session: Session = Depends(get_session)):
    return get_voice_guide(session)


@router.put("/voice", response_model=VoiceGuideRead)
def update_voice(payload: VoiceGuideIn, session: Session = Depends(get_session)):
    guide = get_voice_guide(session)
    for key, value in payload.model_dump().items():
        setattr(guide, key, value)
    guide.updated_at = datetime.now(timezone.utc)
    session.add(guide)
    session.commit()
    session.refresh(guide)
    return guide
