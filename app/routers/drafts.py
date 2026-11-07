import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select

from app.db import get_session
from app.models import Draft, Schedule
from app.schemas.drafts import DraftCreate, DraftRead, DraftUpdate, ScheduleCreate, ScheduleRead

router = APIRouter()


@router.get("/drafts", response_model=list[DraftRead])
def list_drafts(session: Session = Depends(get_session)):
    return session.exec(select(Draft).order_by(Draft.updated_at.desc())).all()


@router.post("/drafts", response_model=DraftRead, status_code=201)
def create_draft(payload: DraftCreate, session: Session = Depends(get_session)):
    data = payload.model_dump()
    data["source_post_ids"] = json.dumps(data["source_post_ids"])
    draft = Draft(**data)
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return draft


@router.get("/drafts/{draft_id}", response_model=DraftRead)
def get_draft(draft_id: int, session: Session = Depends(get_session)):
    draft = session.get(Draft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="draft not found")
    return draft


@router.patch("/drafts/{draft_id}", response_model=DraftRead)
def update_draft(
    draft_id: int, payload: DraftUpdate, session: Session = Depends(get_session)
):
    draft = session.get(Draft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="draft not found")
    data = payload.model_dump(exclude_unset=True)
    if "source_post_ids" in data:
        data["source_post_ids"] = json.dumps(data["source_post_ids"])
    for key, value in data.items():
        setattr(draft, key, value)
    draft.updated_at = datetime.now(timezone.utc)
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return draft


@router.delete("/drafts/{draft_id}", status_code=204)
def delete_draft(draft_id: int, session: Session = Depends(get_session)):
    draft = session.get(Draft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="draft not found")
    session.delete(draft)
    session.commit()
    return Response(status_code=204)


@router.post("/drafts/{draft_id}/schedule", response_model=ScheduleRead, status_code=201)
def schedule_draft(
    draft_id: int,
    payload: ScheduleCreate,
    session: Session = Depends(get_session),
):
    draft = session.get(Draft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="draft not found")
    schedule = Schedule(
        draft_id=draft_id,
        scheduled_at_utc=payload.scheduled_at,
        timezone=payload.timezone,
    )
    draft.status = "scheduled"
    session.add(schedule)
    session.add(draft)
    session.commit()
    session.refresh(schedule)
    return schedule
