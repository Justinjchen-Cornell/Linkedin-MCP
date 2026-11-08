from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SeriesCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=80)
    cadence: str = "weekly"
    weekday: int = Field(default=0, ge=0, le=6)
    template: str = ""
    active: bool = True


class SeriesUpdate(BaseModel):
    name: str | None = None
    cadence: str | None = None
    weekday: int | None = Field(default=None, ge=0, le=6)
    template: str | None = None
    next_number: int | None = Field(default=None, ge=1)
    active: bool | None = None


class SeriesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    cadence: str
    weekday: int
    template: str
    next_number: int
    active: bool
    created_at: datetime
