from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlmodel import Session, select

from app.db import get_session
from app.models import Person

router = APIRouter()


@router.get("/people")
def list_people(
    q: str = "",
    limit: int = 20,
    offset: int = 0,
    session: Session = Depends(get_session),
) -> dict:
    stmt = select(Person)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Person.name.like(like), Person.headline.like(like), Person.company.like(like))
        )
    people = session.exec(stmt.order_by(Person.last_seen_at.desc())).all()
    return {"items": people[offset : offset + limit], "total": len(people)}
