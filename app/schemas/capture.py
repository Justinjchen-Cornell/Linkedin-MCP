from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class CapturedCommentIn(BaseModel):
    author_name: str = ""
    author_url: str | None = None
    text: str = ""
    created_at: datetime | None = None
    reactions: int = 0


class CapturedPostIn(BaseModel):
    urn: str | None = None
    url: str | None = None
    author_name: str = ""
    author_url: str | None = None
    author_headline: str | None = None
    text: str = ""
    posted_at: datetime | None = None
    reactions: int = 0
    comments_count: int = 0
    reposts: int = 0
    media: list[dict[str, Any]] = Field(default_factory=list)
    source: Literal["feed", "search", "hashtag", "profile", "analytics"] = "feed"
    keyword: str | None = None
    raw_html: str | None = None
    comments: list[CapturedCommentIn] = Field(default_factory=list)
    impressions: int | None = None

    @field_validator("raw_html")
    @classmethod
    def truncate_raw_html(cls, value: str | None) -> str | None:
        if value and len(value) > 200_000:
            return value[:200_000]
        return value


class CapturePayload(BaseModel):
    page_url: str = ""
    page_type: str = "feed"
    captured_at: datetime | None = None
    posts: list[CapturedPostIn] = Field(default_factory=list, max_length=100)
