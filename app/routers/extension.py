import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import get_session
from app.models import AccountSnapshot, CapturedPost, FetchJob, PostMetric
from app.schemas.analytics import AccountSnapshotIn, PostMetricIn
from app.schemas.capture import CapturePayload
from app.services.capture import ingest_capture
from app.services.settings import get_setting, set_setting

router = APIRouter()


class PollRequest(BaseModel):
    extension_version: str = ""
    last_seen: str | None = None


@router.post("/extension/capture")
def capture(payload: CapturePayload, session: Session = Depends(get_session)) -> dict:
    result = ingest_capture(session, payload)
    return {
        "inserted": result.inserted,
        "updated": result.updated,
        "skipped": result.skipped,
        "post_ids": result.post_ids,
    }


@router.post("/extension/poll")
def poll(payload: PollRequest, session: Session = Depends(get_session)) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    set_setting(session, "extension_last_seen", now)
    session.commit()
    return {"tasks": [], "server_time": now}


@router.get("/extension/status")
def status(session: Session = Depends(get_session)) -> dict:
    last_seen = get_setting(session, "extension_last_seen") or None
    posts = session.exec(select(CapturedPost)).all()
    return {"last_seen": last_seen, "captured_posts": len(posts)}


@router.post("/extension/account-snapshot")
def ingest_account_snapshot(
    payload: AccountSnapshotIn, session: Session = Depends(get_session)
):
    data = payload.model_dump()
    captured_at = data.pop("captured_at") or datetime.now(timezone.utc)
    snapshot = AccountSnapshot(captured_at=captured_at, **data)
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot


@router.post("/extension/post-metrics")
def ingest_post_metrics(
    payload: list[PostMetricIn], session: Session = Depends(get_session)
) -> dict:
    inserted = 0
    for metric in payload:
        data = metric.model_dump()
        urn = data.pop("urn", None)
        captured_at = data.pop("captured_at") or datetime.now(timezone.utc)
        post_id = None
        if urn:
            post = session.exec(select(CapturedPost).where(CapturedPost.urn == urn)).first()
            if post:
                post_id = post.id
        session.add(
            PostMetric(
                post_id=post_id,
                urn=urn,
                captured_at=captured_at,
                **data,
            )
        )
        inserted += 1
    session.commit()
    return {"inserted": inserted}


@router.get("/extension/jobs/next")
def next_fetch_job(session: Session = Depends(get_session)):
    job = session.exec(
        select(FetchJob).where(FetchJob.status == "queued").order_by(FetchJob.id)
    ).first()
    if job is None:
        return {"job": None}
    job.status = "running"
    job.updated_at = datetime.now(timezone.utc)
    session.add(job)
    session.commit()
    session.refresh(job)
    return {
        "job": {
            "id": job.id,
            "type": job.type,
            "url": job.url,
            "source": job.source,
            "status": job.status,
        }
    }


@router.post("/extension/jobs/{job_id}/result")
def finish_fetch_job(
    job_id: int, payload: dict, session: Session = Depends(get_session)
) -> dict:
    job = session.get(FetchJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    if not payload.get("ok"):
        job.status = "failed"
        job.error = str(payload.get("error") or "fetch failed")[:1000]
        job.updated_at = datetime.now(timezone.utc)
        session.add(job)
        session.commit()
        return {"ok": True, "status": job.status}

    result = payload.get("result") or {}
    try:
        if job.type == "profile":
            snapshot_data = result.get("snapshot") or {}
            session.add(
                AccountSnapshot(
                    followers=snapshot_data.get("followers"),
                    connections=snapshot_data.get("connections"),
                    profile_views=snapshot_data.get("profile_views"),
                    post_impressions_7d=snapshot_data.get("post_impressions_7d"),
                    search_appearances_7d=snapshot_data.get("search_appearances_7d"),
                    raw_text=snapshot_data.get("raw_text"),
                )
            )
            capture_result = ingest_capture(
                session,
                CapturePayload(
                    page_url=result.get("page_url", job.url),
                    page_type="profile",
                    posts=result.get("posts") or [],
                ),
            )
            job.result_json = json.dumps(
                {
                    "snapshot": snapshot_data,
                    "inserted": capture_result.inserted,
                    "updated": capture_result.updated,
                    "post_ids": capture_result.post_ids,
                },
                ensure_ascii=False,
            )
        elif job.type == "post_metrics":
            metric_data = result.get("metrics") or {}
            urn = metric_data.get("urn")
            post_id = None
            if urn:
                post = session.exec(
                    select(CapturedPost).where(CapturedPost.urn == urn)
                ).first()
                if post:
                    post_id = post.id
            session.add(
                PostMetric(
                    post_id=post_id,
                    urn=urn,
                    impressions=metric_data.get("impressions"),
                    members_reached=metric_data.get("members_reached"),
                    in_network_pct=metric_data.get("in_network_pct"),
                    out_network_pct=metric_data.get("out_network_pct"),
                    profile_viewers=metric_data.get("profile_viewers"),
                    followers_gained=metric_data.get("followers_gained"),
                    social_engagements=metric_data.get("social_engagements"),
                    reactions=metric_data.get("reactions"),
                    comments=metric_data.get("comments"),
                    reposts=metric_data.get("reposts"),
                    saves=metric_data.get("saves"),
                    sends=metric_data.get("sends"),
                    raw_text=metric_data.get("raw_text"),
                )
            )
            session.commit()
            job.result_json = json.dumps(metric_data, ensure_ascii=False)
        elif job.type == "page":
            capture_payload = result.get("payload") or {}
            capture_result = ingest_capture(
                session,
                CapturePayload(
                    page_url=capture_payload.get("page_url", job.url),
                    page_type=capture_payload.get("page_type", "feed"),
                    posts=capture_payload.get("posts") or [],
                ),
            )
            job.result_json = json.dumps(
                {
                    "inserted": capture_result.inserted,
                    "updated": capture_result.updated,
                    "post_ids": capture_result.post_ids,
                },
                ensure_ascii=False,
            )
        else:
            raise ValueError("unsupported job type")
        job.status = "done"
        job.error = None
    except Exception as error:
        job.status = "failed"
        job.error = str(error)[:1000]
    job.updated_at = datetime.now(timezone.utc)
    session.add(job)
    session.commit()
    return {"ok": True, "status": job.status}
