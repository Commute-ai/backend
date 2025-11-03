from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PreferenceBase(BaseModel):
    prompt: str


class PreferenceCreate(PreferenceBase):
    pass


class PreferenceResponse(PreferenceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
