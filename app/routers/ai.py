import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.db import get_session
from app.services import ai_config
from app.services.ai import AIConfigError, generate_variants
from app.services.settings import get_setting, set_setting
from app.services.style_profile import build_style_profile

router = APIRouter()


class AIConfigPayload(BaseModel):
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    api_key: str | None = None


class GeneratePayload(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    source_post_ids: list[int] = Field(default_factory=list)
    angle: str = ""
    language: str = "en"
    count: int = Field(default=3, ge=1, le=5)


@router.get("/ai/config")
def read_ai_config(session: Session = Depends(get_session)) -> dict:
    return {
        "base_url": get_setting(session, "ai_base_url", "https://api.deepseek.com"),
        "model": get_setting(session, "ai_model", "deepseek-chat"),
        "has_key": bool(ai_config.get_api_key()),
    }


@router.put("/ai/config")
def update_ai_config(
    payload: AIConfigPayload, session: Session = Depends(get_session)
) -> dict:
    set_setting(session, "ai_base_url", payload.base_url.strip())
    set_setting(session, "ai_model", payload.model.strip())
    session.commit()
    if payload.api_key is not None:
        ai_config.set_api_key(payload.api_key.strip())
    return {"ok": True}


@router.get("/ai/style-profile")
def read_style_profile(session: Session = Depends(get_session)) -> dict:
    return build_style_profile(session)


@router.post("/ai/generate")
def generate(payload: GeneratePayload, session: Session = Depends(get_session)) -> dict:
    try:
        return generate_variants(
            session,
            topic=payload.topic,
            source_post_ids=payload.source_post_ids,
            angle=payload.angle,
            language=payload.language,
            count=payload.count,
        )
    except AIConfigError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except httpx.HTTPError as error:
        raise HTTPException(status_code=502, detail=f"AI 服务请求失败：{error}") from error
