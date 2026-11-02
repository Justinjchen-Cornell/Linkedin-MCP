from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.db import init_db
from app.routers import health

app = FastAPI(title="LinkedIn Workbench")
init_db()
app.include_router(health.router, prefix="/api")

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
