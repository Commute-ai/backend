from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class GlobalPreferenceBase(BaseModel):
    prompt: str


class GlobalPreferenceCreate(GlobalPreferenceBase):
    pass


class GlobalPreferenceResponse(GlobalPreferenceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
