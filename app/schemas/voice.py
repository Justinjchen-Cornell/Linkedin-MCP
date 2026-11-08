from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VoiceGuideIn(BaseModel):
    beliefs: str = ""
    signature_phrases: str = ""
    banned_phrases: str = ""
    data_sources: str = ""
    stories: str = ""


class VoiceGuideRead(VoiceGuideIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: datetime
