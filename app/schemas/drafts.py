from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DraftCreate(BaseModel):
    title: str = ""
    body: str = Field(default="", max_length=3000)
    language: str = "en"
    source_post_ids: list[int] = Field(default_factory=list)
    hook_type: str | None = None


class DraftUpdate(BaseModel):
    title: str | None = None
    body: str | None = Field(default=None, max_length=3000)
    language: str | None = None
    status: str | None = None
    source_post_ids: list[int] | None = None
    hook_type: str | None = None


class DraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str
    language: str
    status: str
    series_id: int | None = None
    issue_number: int | None = None
    kind: str = "deep"
    parent_draft_id: int | None = None
    source_post_ids: str
    hook_type: str | None = None
    ai_run_id: int | None = None
    created_at: datetime
    updated_at: datetime


class ScheduleCreate(BaseModel):
    scheduled_at: datetime
    timezone: str = "Asia/Shanghai"


class ScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    draft_id: int
    scheduled_at_utc: datetime
    timezone: str
    status: str
    notified_at: datetime | None = None
    opened_at: datetime | None = None
    published_at: datetime | None = None
    published_url: str | None = None
    error: str | None = None
    created_at: datetime
