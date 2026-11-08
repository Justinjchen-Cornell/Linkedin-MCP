from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select

from app.db import get_session
from app.models import Series
from app.schemas.series import SeriesCreate, SeriesRead, SeriesUpdate

router = APIRouter()


@router.get("/series", response_model=list[SeriesRead])
def list_series(session: Session = Depends(get_session)):
    return session.exec(select(Series).order_by(Series.weekday)).all()


@router.post("/series", response_model=SeriesRead, status_code=201)
def create_series(payload: SeriesCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(Series).where(Series.slug == payload.slug)).first()
    if existing:
        raise HTTPException(status_code=409, detail="series slug already exists")
    series = Series(**payload.model_dump())
    session.add(series)
    session.commit()
    session.refresh(series)
    return series


@router.patch("/series/{series_id}", response_model=SeriesRead)
def update_series(
    series_id: int, payload: SeriesUpdate, session: Session = Depends(get_session)
):
    series = session.get(Series, series_id)
    if series is None:
        raise HTTPException(status_code=404, detail="series not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(series, key, value)
    session.add(series)
    session.commit()
    session.refresh(series)
    return series


@router.delete("/series/{series_id}", status_code=204)
def delete_series(series_id: int, session: Session = Depends(get_session)):
    series = session.get(Series, series_id)
    if series is None:
        raise HTTPException(status_code=404, detail="series not found")
    session.delete(series)
    session.commit()
    return Response(status_code=204)
