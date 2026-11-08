import json
import re
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


def _sentences(text: str) -> list[str]:
    parts: list[str] = []
    for line in text.splitlines():
        parts.extend(re.split(r"(?<=[.!?。！？])\s+", line.strip()))
    return [part.strip() for part in parts if part.strip()]


def _first_data_sentence(text: str) -> str:
    for sentence in _sentences(text):
        if any(char.isdigit() for char in sentence) and len(sentence) >= 8:
            return sentence
    return text.strip()[:200] or "（待补充数据点）"


def _opinion_sentence(text: str) -> str:
    for sentence in _sentences(text):
        lowered = sentence.lower()
        if any(
            marker in lowered
            for marker in ["my view", "i think", "i believe", "我认为", "我的判断", "关键是"]
        ):
            return sentence
    sentences = _sentences(text)
    return sentences[0] if sentences else "（待补充观点）"


@router.post("/drafts/{draft_id}/derive")
def derive_light_drafts(draft_id: int, session: Session = Depends(get_session)):
    draft = session.get(Draft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="draft not found")

    data_sentence = _first_data_sentence(draft.body)
    opinion = _opinion_sentence(draft.body)
    data_body = f"{data_sentence}\n\n这对我的配置意味着什么：先看信用和流动性，不急着追价格。\n\n#数据 #宏观"[:3000]
    opinion_body = f"{opinion}\n\n你怎么看？\n\n#观点 #宏观"[:3000]

    items = [
        Draft(
            title=f"数据卡：{draft.title or '深度拆解'}",
            body=data_body,
            language=draft.language,
            kind="light",
            parent_draft_id=draft.id,
            series_id=draft.series_id,
        ),
        Draft(
            title=f"观点：{draft.title or '深度拆解'}",
            body=opinion_body,
            language=draft.language,
            kind="light",
            parent_draft_id=draft.id,
            series_id=draft.series_id,
        ),
    ]
    for item in items:
        session.add(item)
    session.commit()
    for item in items:
        session.refresh(item)
    return {"items": items}
