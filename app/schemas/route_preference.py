from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RoutePreferenceBase(BaseModel):
    prompt: str
    from_latitude: float = Field(..., ge=-90, le=90)
    from_longitude: float = Field(..., ge=-180, le=180)
    to_latitude: float = Field(..., ge=-90, le=90)
    to_longitude: float = Field(..., ge=-180, le=180)


class RoutePreferenceCreate(RoutePreferenceBase):
    pass


class RoutePreferenceResponse(RoutePreferenceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
