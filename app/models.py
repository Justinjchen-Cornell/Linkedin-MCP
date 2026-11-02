from datetime import datetime, timezone

from sqlmodel import Field, SQLModel, UniqueConstraint


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CapturedPost(SQLModel, table=True):
    __tablename__ = "captured_posts"

    id: int | None = Field(default=None, primary_key=True)
    urn: str | None = Field(default=None, index=True)
    url: str | None = Field(default=None, index=True)
    author_name: str = ""
    author_url: str | None = None
    author_headline: str | None = None
    text: str = ""
    posted_at: datetime | None = None
    reactions: int = 0
    comments_count: int = 0
    reposts: int = 0
    media_json: str = "[]"
    source: str = "feed"
    keyword: str | None = None
    raw_html: str | None = None
    parser_version: str = "1"
    content_hash: str = Field(index=True)
    is_own: bool = False
    first_captured_at: datetime = Field(default_factory=utcnow)
    last_captured_at: datetime = Field(default_factory=utcnow)
    heat_score: float = 0.0


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="captured_posts.id", index=True)
    author_name: str = ""
    author_url: str | None = None
    text: str = ""
    created_at: datetime | None = None
    reactions: int = 0
    captured_at: datetime = Field(default_factory=utcnow)


class Person(SQLModel, table=True):
    __tablename__ = "people"

    id: int | None = Field(default=None, primary_key=True)
    name: str = ""
    url: str | None = Field(default=None, unique=True, index=True)
    headline: str | None = None
    company: str | None = None
    first_seen_at: datetime = Field(default_factory=utcnow)
    last_seen_at: datetime = Field(default_factory=utcnow)
    notes: str | None = None


class WatchlistItem(SQLModel, table=True):
    __tablename__ = "watchlist"
    __table_args__ = (UniqueConstraint("kind", "value", name="uq_watchlist_kind_value"),)

    id: int | None = Field(default=None, primary_key=True)
    kind: str
    value: str
    active: bool = True
    last_run_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)


class Setting(SQLModel, table=True):
    __tablename__ = "settings"

    key: str = Field(primary_key=True)
    value: str = ""


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: int | None = Field(default=None, primary_key=True)
    level: str = "info"
    source: str = ""
    message: str = ""
    detail_json: str = "{}"
    created_at: datetime = Field(default_factory=utcnow)
