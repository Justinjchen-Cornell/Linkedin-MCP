from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import Setting
from app.services.settings import set_setting

router = APIRouter()


@router.get("/settings")
def read_settings(session: Session = Depends(get_session)) -> dict[str, str]:
    rows = session.exec(select(Setting)).all()
    return {row.key: row.value for row in rows}


@router.put("/settings")
def update_settings(
    payload: dict[str, str], session: Session = Depends(get_session)
) -> dict[str, str]:
    for key, value in payload.items():
        set_setting(session, key, value)
    session.commit()
    rows = session.exec(select(Setting)).all()
    return {row.key: row.value for row in rows}
