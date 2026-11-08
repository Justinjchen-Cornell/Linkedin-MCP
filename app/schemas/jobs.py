from pydantic import BaseModel, Field


class FetchRequest(BaseModel):
    type: str
    url: str | None = None
    post_id: int | None = None
    urn: str | None = None
    source: str | None = None
    limit: int = Field(default=10, ge=1, le=50)
    sync: bool = False
    timeout: int = Field(default=90, ge=2, le=120)
