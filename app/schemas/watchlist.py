from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WatchlistItemCreate(BaseModel):
    kind: str
    value: str
    active: bool = True


class WatchlistItemUpdate(BaseModel):
    value: str | None = None
    active: bool | None = None


class WatchlistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    value: str
    active: bool
    last_run_at: datetime | None = None
    created_at: datetime
