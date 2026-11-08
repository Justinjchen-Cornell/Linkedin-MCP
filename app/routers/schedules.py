from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Draft, Schedule
from app.schemas.drafts import ScheduleRead

router = APIRouter()


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


@router.get("/schedules")
def list_schedules(
    status: str | None = None, session: Session = Depends(get_session)
) -> dict:
    stmt = select(Schedule)
    if status:
        stmt = stmt.where(Schedule.status == status)
    items = session.exec(stmt.order_by(Schedule.scheduled_at_utc)).all()
    return {"items": items}


@router.get("/schedules/due")
def due_schedules(session: Session = Depends(get_session)) -> dict:
    now = datetime.now(timezone.utc)
    items = session.exec(
        select(Schedule)
        .where(Schedule.status == "scheduled")
        .order_by(Schedule.scheduled_at_utc)
    ).all()
    return {"items": [item for item in items if _aware(item.scheduled_at_utc) <= now]}


@router.post("/schedules/{schedule_id}/opened", response_model=ScheduleRead)
def mark_opened(schedule_id: int, session: Session = Depends(get_session)):
    schedule = session.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="schedule not found")
    schedule.opened_at = datetime.now(timezone.utc)
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return schedule


@router.post("/schedules/{schedule_id}/notified", response_model=ScheduleRead)
def mark_notified(schedule_id: int, session: Session = Depends(get_session)):
    schedule = session.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="schedule not found")
    schedule.notified_at = datetime.now(timezone.utc)
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return schedule


@router.post("/schedules/{schedule_id}/skipped", response_model=ScheduleRead)
def mark_skipped(schedule_id: int, session: Session = Depends(get_session)):
    schedule = session.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="schedule not found")
    schedule.status = "skipped"
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return schedule


@router.post("/schedules/{schedule_id}/published", response_model=ScheduleRead)
def mark_published(
    schedule_id: int,
    payload: dict | None = None,
    session: Session = Depends(get_session),
):
    schedule = session.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="schedule not found")
    schedule.status = "published"
    schedule.published_at = datetime.now(timezone.utc)
    if payload and payload.get("published_url"):
        schedule.published_url = payload["published_url"]
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return schedule


@router.get("/schedules/{schedule_id}")
def get_schedule(schedule_id: int, session: Session = Depends(get_session)) -> dict:
    schedule = session.get(Schedule, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="schedule not found")
    draft = session.get(Draft, schedule.draft_id)
    return {
        "id": schedule.id,
        "draft_id": schedule.draft_id,
        "scheduled_at_utc": schedule.scheduled_at_utc,
        "timezone": schedule.timezone,
        "status": schedule.status,
        "draft_title": draft.title if draft else "",
        "draft_body": draft.body if draft else "",
        "image_url": (
            f"/api/drafts/{draft.id}/image" if draft and draft.image_path else None
        ),
    }
