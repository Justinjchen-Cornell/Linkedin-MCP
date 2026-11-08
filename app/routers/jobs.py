import json

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import CapturedPost, FetchJob
from app.schemas.jobs import FetchRequest
from app.services.settings import get_setting

router = APIRouter()


def _post_summary_url(urn: str) -> str:
    return f"https://www.linkedin.com/analytics/post-summary/{urn}/"


def _create_job(session: Session, job_type: str, url: str, source: str | None = None) -> FetchJob:
    job = FetchJob(type=job_type, url=url, source=source)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@router.post("/fetch", status_code=202)
def create_fetch(payload: FetchRequest, session: Session = Depends(get_session)):
    if payload.type == "profile":
        url = get_setting(session, "own_profile_url", "")
        if not url:
            raise HTTPException(status_code=400, detail="own_profile_url is not configured")
        job = _create_job(session, "profile", url)
        return {"id": job.id, "status": job.status, "type": job.type}

    if payload.type in {"post_metrics", "page"}:
        url = payload.url or ""
        if not url.startswith("https://www.linkedin.com/"):
            raise HTTPException(status_code=400, detail="url must be a LinkedIn URL")
        if payload.type == "post_metrics" and "analytics/post-summary/" not in url:
            raise HTTPException(status_code=400, detail="url must be a post-summary URL")
        job = _create_job(session, payload.type, url, payload.source)
        return {"id": job.id, "status": job.status, "type": job.type}

    if payload.type == "all_post_metrics":
        posts = session.exec(
            select(CapturedPost)
            .where(CapturedPost.urn != None)  # noqa: E711
            .order_by(CapturedPost.id.desc())
            .limit(payload.limit)
        ).all()
        jobs = [_create_job(session, "post_metrics", _post_summary_url(post.urn)) for post in posts]
        return {"jobs": [{"id": job.id, "status": job.status} for job in jobs]}

    raise HTTPException(status_code=400, detail="unsupported fetch type")


@router.post("/posts/{post_id}/fetch", status_code=202)
def fetch_post_metrics(post_id: int, session: Session = Depends(get_session)):
    post = session.get(CapturedPost, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    if not post.urn:
        raise HTTPException(status_code=400, detail="post has no LinkedIn urn")
    job = _create_job(session, "post_metrics", _post_summary_url(post.urn))
    return {"id": job.id, "status": job.status, "type": job.type}


@router.get("/jobs/{job_id}")
def get_job(job_id: int, session: Session = Depends(get_session)) -> dict:
    job = session.get(FetchJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "id": job.id,
        "type": job.type,
        "url": job.url,
        "status": job.status,
        "error": job.error,
        "result": json.loads(job.result_json) if job.result_json else None,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


@router.get("/jobs")
def list_jobs(limit: int = 20, session: Session = Depends(get_session)) -> dict:
    jobs = session.exec(select(FetchJob).order_by(FetchJob.id.desc()).limit(limit)).all()
    return {
        "items": [
            {
                "id": job.id,
                "type": job.type,
                "url": job.url,
                "status": job.status,
                "error": job.error,
                "created_at": job.created_at,
            }
            for job in jobs
        ],
        "total": len(jobs),
    }
