from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PreferenceBase(BaseModel):
    preference: str


class PreferenceCreate(PreferenceBase):
    user_id: int


class PreferenceResponse(PreferenceBase):
    created_at: datetime
    updated_at: Optional[datetime] = None
