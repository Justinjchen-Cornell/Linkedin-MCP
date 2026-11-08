from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Draft, Series
from app.schemas.drafts import DraftRead

router = APIRouter()


@router.post("/series/{series_id}/next-issue", response_model=DraftRead)
def next_issue(series_id: int, session: Session = Depends(get_session)):
    series = session.get(Series, series_id)
    if series is None:
        raise HTTPException(status_code=404, detail="series not found")
    issue = series.next_number
    draft = Draft(
        title=f"{series.name} #{issue}",
        body=series.template,
        series_id=series.id,
        issue_number=issue,
        kind="deep",
    )
    series.next_number = issue + 1
    session.add(draft)
    session.add(series)
    session.commit()
    session.refresh(draft)
    return draft


@router.get("/plan/week")
def week_plan(start: str | None = None, session: Session = Depends(get_session)) -> dict:
    if start:
        week_start = date.fromisoformat(start)
        week_start = week_start - timedelta(days=week_start.weekday())
    else:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

    series_list = session.exec(select(Series).where(Series.active == True)).all()  # noqa: E712
    drafts = session.exec(select(Draft).where(Draft.series_id != None)).all()  # noqa: E711

    slots = []
    warnings = []
    for index in range(5):
        slot_date = week_start + timedelta(days=index)
        series = next((item for item in series_list if item.weekday == index), None)
        if series:
            existing = next(
                (
                    draft
                    for draft in drafts
                    if draft.series_id == series.id
                    and draft.issue_number == series.next_number - 1
                    and draft.status in {"draft", "scheduled"}
                ),
                None,
            )
            issue = existing.issue_number if existing else series.next_number
            slots.append(
                {
                    "date": slot_date.isoformat(),
                    "kind": "deep",
                    "series_id": series.id,
                    "series_name": series.name,
                    "issue_number": issue,
                    "title": f"{series.name} #{issue}",
                    "status": existing.status if existing else "planned",
                    "draft_id": existing.id if existing else None,
                }
            )
        else:
            title = "数据卡" if index % 2 == 1 else "观点/问题"
            slots.append(
                {
                    "date": slot_date.isoformat(),
                    "kind": "light",
                    "series_name": None,
                    "issue_number": None,
                    "title": title,
                    "status": "planned",
                    "draft_id": None,
                }
            )

    for series in series_list:
        if series.weekday > 4:
            warnings.append(f"{series.name} 排在周末，本周不会出现")
    for index in range(5):
        matching = [item for item in series_list if item.weekday == index]
        if len(matching) > 1:
            warnings.append(f"周{index + 1} 有 {len(matching)} 个系列，只显示第一个")

    return {"week_start": week_start.isoformat(), "slots": slots, "warnings": warnings}
