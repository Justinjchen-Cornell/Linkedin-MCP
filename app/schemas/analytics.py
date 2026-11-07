from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AccountSnapshotIn(BaseModel):
    captured_at: datetime | None = None
    followers: int | None = None
    connections: int | None = None
    profile_views: int | None = None
    post_impressions_7d: int | None = None
    search_appearances_7d: int | None = None
    raw_text: str | None = None


class AccountSnapshotRead(AccountSnapshotIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PostMetricIn(BaseModel):
    urn: str | None = None
    captured_at: datetime | None = None
    impressions: int | None = None
    members_reached: int | None = None
    in_network_pct: float | None = None
    out_network_pct: float | None = None
    profile_viewers: int | None = None
    followers_gained: int | None = None
    social_engagements: int | None = None
    reactions: int | None = None
    comments: int | None = None
    reposts: int | None = None
    saves: int | None = None
    sends: int | None = None
    raw_text: str | None = None


class PostMetricRead(PostMetricIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    post_id: int | None = None
