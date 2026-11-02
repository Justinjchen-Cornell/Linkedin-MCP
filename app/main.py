from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app import models  # noqa: F401
from app.db import get_session, init_db
from app.routers import extension, health, people, posts, settings, watchlist
from app.routers.posts import get_post, list_posts

app = FastAPI(title="LinkedIn Workbench")
init_db()
app.include_router(health.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")
app.include_router(extension.router, prefix="/api")
app.include_router(posts.router, prefix="/api")
app.include_router(people.router, prefix="/api")

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
