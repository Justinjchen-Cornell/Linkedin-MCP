from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app import models  # noqa: F401
from app.db import get_session, init_db
from app.routers import ai, analytics, drafts, extension, health, people, posts, schedules, settings, watchlist
from app.models import Setting, WatchlistItem
from app.routers.posts import get_post, list_posts
from app.services import ai_config
from app.services.analytics import latest_post_metrics, overview as analytics_overview
from app.services.settings import set_setting

app = FastAPI(title="LinkedIn Workbench")
init_db()
app.include_router(health.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")
app.include_router(extension.router, prefix="/api")
app.include_router(posts.router, prefix="/api")
app.include_router(people.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(drafts.router, prefix="/api")
app.include_router(schedules.router, prefix="/api")
app.include_router(ai.router, prefix="/api")

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

ALLOWED_ORIGINS = (
    "chrome-extension://",
    "http://127.0.0.1:8765",
    "http://localhost:8765",
)


@app.middleware("http")
async def origin_guard(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        if origin and not origin.startswith(ALLOWED_ORIGINS):
            return JSONResponse({"detail": "cross-origin write blocked"}, status_code=403)
    return await call_next(request)


@app.get("/")
def index() -> RedirectResponse:
    return RedirectResponse("/posts", status_code=307)


@app.get("/posts", response_class=HTMLResponse)
def posts_page(
    request: Request,
    q: str = "",
    source: str | None = None,
    own: bool | None = None,
    sort: str = "new",
    limit: int = 20,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    data = list_posts(
        q=q,
        source=source,
        own=own,
        min_reactions=0,
        sort=sort,
        limit=limit,
        offset=offset,
        session=session,
    )
    return templates.TemplateResponse(
        request=request,
        name="posts.html",
        context={
            "posts": data["items"],
            "total": data["total"],
            "filters": {"q": q, "source": source, "own": own, "sort": sort},
            "limit": limit,
            "offset": offset,
        },
    )


@app.get("/posts/{post_id}", response_class=HTMLResponse)
def post_page(
    request: Request,
    post_id: int,
    session: Session = Depends(get_session),
):
    data = get_post(post_id, session)
    return templates.TemplateResponse(
        request=request,
        name="post_detail.html",
        context={"post": data, "comments": data["comments"]},
    )


@app.get("/settings", response_class=HTMLResponse)
def settings_page(
    request: Request,
    session: Session = Depends(get_session),
):
    values = {row.key: row.value for row in session.exec(select(Setting)).all()}
    items = session.exec(select(WatchlistItem).order_by(WatchlistItem.id)).all()
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "values": values,
            "watchlist": items,
            "has_ai_key": bool(ai_config.get_api_key()),
        },
    )


@app.post("/settings")
def save_settings(
    own_profile_url: str = Form(""),
    capture_scroll_screens: str = Form("3"),
    max_posts_per_capture: str = Form("100"),
    analytics_sync_hour: str = Form("9"),
    ai_base_url: str = Form("https://api.deepseek.com"),
    ai_model: str = Form("deepseek-chat"),
    ai_api_key: str = Form(""),
    session: Session = Depends(get_session),
) -> RedirectResponse:
    set_setting(session, "own_profile_url", own_profile_url.strip())
    set_setting(session, "capture_scroll_screens", capture_scroll_screens)
    set_setting(session, "max_posts_per_capture", max_posts_per_capture)
    set_setting(session, "analytics_sync_hour", analytics_sync_hour)
    set_setting(session, "ai_base_url", ai_base_url.strip())
    set_setting(session, "ai_model", ai_model.strip())
    if ai_api_key.strip():
        ai_config.set_api_key(ai_api_key.strip())
    session.commit()
    return RedirectResponse("/settings", status_code=303)


@app.post("/watchlist")
def add_watchlist_form(
    kind: str = Form(...),
    value: str = Form(...),
    session: Session = Depends(get_session),
) -> RedirectResponse:
    value = value.strip()
    if value:
        existing = session.exec(
            select(WatchlistItem).where(
                WatchlistItem.kind == kind,
                WatchlistItem.value == value,
            )
        ).first()
        if existing is None:
            session.add(WatchlistItem(kind=kind, value=value))
            session.commit()
    return RedirectResponse("/settings", status_code=303)


@app.post("/watchlist/{item_id}/delete")
def delete_watchlist_form(
    item_id: int,
    session: Session = Depends(get_session),
) -> RedirectResponse:
    item = session.get(WatchlistItem, item_id)
    if item is not None:
        session.delete(item)
        session.commit()
    return RedirectResponse("/settings", status_code=303)


@app.get("/analytics", response_class=HTMLResponse)
def analytics_page(request: Request, session: Session = Depends(get_session)):
    data = analytics_overview(session)
    posts = latest_post_metrics(session)
    return templates.TemplateResponse(
        request=request,
        name="analytics.html",
        context={"overview": data, "posts": posts},
    )
