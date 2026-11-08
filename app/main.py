from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app import models  # noqa: F401
from app.db import get_session, init_db
from app.routers import ai, analytics, api_v1, drafts, extension, health, jobs, people, plan, posts, schedules, series, settings, voice, watchlist
from app.models import Draft, Schedule, Series, Setting, WatchlistItem
from app.routers.drafts import upload_draft_image
from app.routers.plan import next_issue as create_next_issue, week_plan
from app.routers.posts import get_post, list_posts
from app.services import ai_config
from app.services.analytics import best_times as get_best_times
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
app.include_router(series.router, prefix="/api")
app.include_router(plan.router, prefix="/api")
app.include_router(voice.router, prefix="/api")
app.include_router(api_v1.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")

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


@app.get("/drafts", response_class=HTMLResponse)
def drafts_page(request: Request, session: Session = Depends(get_session)):
    drafts = session.exec(select(Draft).order_by(Draft.updated_at.desc())).all()
    return templates.TemplateResponse(
        request=request,
        name="drafts.html",
        context={"drafts": drafts},
    )


@app.post("/drafts")
def create_draft_form(
    title: str = Form(""), body: str = Form(""), session: Session = Depends(get_session)
):
    if len(body) > 3000:
        raise HTTPException(status_code=422, detail="body exceeds 3000 characters")
    draft = Draft(title=title.strip(), body=body)
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return RedirectResponse(f"/drafts/{draft.id}", status_code=303)


@app.get("/drafts/{draft_id}", response_class=HTMLResponse)
def draft_editor_page(
    request: Request, draft_id: int, session: Session = Depends(get_session)
):
    draft = session.get(Draft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="draft not found")
    return templates.TemplateResponse(
        request=request,
        name="draft_editor.html",
        context={"draft": draft, "best_times": get_best_times(session)},
    )


@app.post("/drafts/{draft_id}")
def save_draft_form(
    draft_id: int,
    title: str = Form(""),
    body: str = Form(""),
    language: str = Form("en"),
    session: Session = Depends(get_session),
):
    draft = session.get(Draft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="draft not found")
    if len(body) > 3000:
        raise HTTPException(status_code=422, detail="body exceeds 3000 characters")
    draft.title = title.strip()
    draft.body = body
    draft.language = language
    draft.updated_at = datetime.now(timezone.utc)
    session.add(draft)
    session.commit()
    return RedirectResponse(f"/drafts/{draft_id}", status_code=303)


@app.get("/calendar", response_class=HTMLResponse)
def calendar_page(request: Request, session: Session = Depends(get_session)):
    schedules = session.exec(select(Schedule).order_by(Schedule.scheduled_at_utc)).all()
    items = []
    for schedule in schedules:
        draft = session.get(Draft, schedule.draft_id)
        if draft:
            local_time = schedule.scheduled_at_utc.replace(tzinfo=timezone.utc).astimezone(
                ZoneInfo(schedule.timezone)
            )
            items.append(
                {
                    "schedule": schedule,
                    "draft": draft,
                    "local_time": local_time.strftime("%Y-%m-%d %H:%M"),
                }
            )
    return templates.TemplateResponse(
        request=request,
        name="calendar.html",
        context={"items": items},
    )


@app.post("/drafts/{draft_id}/schedule")
def schedule_draft_form(
    draft_id: int,
    scheduled_at: str = Form(...),
    session: Session = Depends(get_session),
):
    draft = session.get(Draft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="draft not found")
    local = datetime.fromisoformat(scheduled_at).replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    schedule = Schedule(
        draft_id=draft_id,
        scheduled_at_utc=local.astimezone(timezone.utc),
        timezone="Asia/Shanghai",
    )
    draft.status = "scheduled"
    session.add(schedule)
    session.add(draft)
    session.commit()
    return RedirectResponse("/calendar", status_code=303)


@app.post("/calendar/{schedule_id}/published")
def publish_schedule_form(
    schedule_id: int, session: Session = Depends(get_session)
):
    schedule = session.get(Schedule, schedule_id)
    if schedule is not None:
        schedule.status = "published"
        schedule.published_at = datetime.now(timezone.utc)
        session.add(schedule)
        session.commit()
    return RedirectResponse("/calendar", status_code=303)


@app.post("/calendar/{schedule_id}/skipped")
def skip_schedule_form(schedule_id: int, session: Session = Depends(get_session)):
    schedule = session.get(Schedule, schedule_id)
    if schedule is not None:
        schedule.status = "skipped"
        session.add(schedule)
        session.commit()
    return RedirectResponse("/calendar", status_code=303)


@app.get("/series", response_class=HTMLResponse)
def series_page(request: Request, session: Session = Depends(get_session)):
    series_list = session.exec(select(Series).order_by(Series.weekday)).all()
    return templates.TemplateResponse(
        request=request,
        name="series.html",
        context={"series_list": series_list},
    )


@app.post("/series")
def create_series_form(
    name: str = Form(...),
    slug: str = Form(...),
    weekday: int = Form(0),
    template: str = Form(""),
    session: Session = Depends(get_session),
):
    if session.exec(select(Series).where(Series.slug == slug)).first():
        raise HTTPException(status_code=409, detail="series slug already exists")
    session.add(
        Series(name=name.strip(), slug=slug.strip(), weekday=weekday, template=template)
    )
    session.commit()
    return RedirectResponse("/series", status_code=303)


@app.post("/series/{series_id}/delete")
def delete_series_form(series_id: int, session: Session = Depends(get_session)):
    series = session.get(Series, series_id)
    if series is not None:
        session.delete(series)
        session.commit()
    return RedirectResponse("/series", status_code=303)


@app.get("/plan", response_class=HTMLResponse)
def plan_page(request: Request, session: Session = Depends(get_session)):
    plan = week_plan(start=None, session=session)
    return templates.TemplateResponse(
        request=request,
        name="plan.html",
        context={"plan": plan},
    )


@app.post("/plan/next-issue/{series_id}")
def plan_next_issue(series_id: int, session: Session = Depends(get_session)):
    draft = create_next_issue(series_id, session)
    return RedirectResponse(f"/drafts/{draft.id}", status_code=303)


@app.post("/plan/light")
def plan_light(
    title: str = Form("轻量"), session: Session = Depends(get_session)
):
    draft = Draft(title=title, body="", kind="light")
    session.add(draft)
    session.commit()
    session.refresh(draft)
    return RedirectResponse(f"/drafts/{draft.id}", status_code=303)


@app.post("/drafts/{draft_id}/image")
def upload_draft_image_form(
    draft_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    upload_draft_image(draft_id, file, session)
    return RedirectResponse(f"/drafts/{draft_id}", status_code=303)
