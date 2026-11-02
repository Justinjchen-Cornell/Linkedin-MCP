from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select

from app.db import get_session
from app.models import WatchlistItem
from app.schemas.watchlist import (
    WatchlistItemCreate,
    WatchlistItemRead,
    WatchlistItemUpdate,
)
from app.services.linkedin_urls import build_search_url

ALLOWED_KINDS = {"keyword", "person", "company", "hashtag"}

router = APIRouter()


@router.get("/watchlist", response_model=list[WatchlistItemRead])
def list_watchlist(session: Session = Depends(get_session)):
    return session.exec(select(WatchlistItem).order_by(WatchlistItem.id)).all()


@router.get("/watchlist/round")
def watchlist_round(limit: int = 5, session: Session = Depends(get_session)) -> dict:
    capped = max(1, min(limit, 5))
    items = session.exec(
        select(WatchlistItem)
        .where(WatchlistItem.active == True)  # noqa: E712
        .order_by(WatchlistItem.id)
    ).all()
    tasks = []
    for item in items:
        try:
            url = build_search_url(item.kind, item.value)
        except ValueError:
            continue
        tasks.append({"id": item.id, "kind": item.kind, "value": item.value, "url": url})
        if len(tasks) >= capped:
            break
    return {"tasks": tasks}


@router.post("/watchlist", response_model=WatchlistItemRead, status_code=201)
def create_watchlist_item(
    payload: WatchlistItemCreate, session: Session = Depends(get_session)
):
    if payload.kind not in ALLOWED_KINDS:
        raise HTTPException(status_code=422, detail="unsupported watchlist kind")
    existing = session.exec(
        select(WatchlistItem).where(
            WatchlistItem.kind == payload.kind,
            WatchlistItem.value == payload.value,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="watchlist item already exists")
    item = WatchlistItem(**payload.model_dump())
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.patch("/watchlist/{item_id}", response_model=WatchlistItemRead)
def update_watchlist_item(
    item_id: int,
    payload: WatchlistItemUpdate,
    session: Session = Depends(get_session),
):
    item = session.get(WatchlistItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="watchlist item not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/watchlist/{item_id}", status_code=204)
def delete_watchlist_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(WatchlistItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="watchlist item not found")
    session.delete(item)
    session.commit()
    return Response(status_code=204)
