"""
Itinerary Schema

Pydantic models for representing transit routes and itineraries.
"""

from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field

from app.schemas.location import Place


class TransportMode(str, Enum):
    """Transport modes."""

    WALK = "WALK"
    BICYCLE = "BICYCLE"
    CAR = "CAR"
    TRAM = "TRAM"
    SUBWAY = "SUBWAY"
    RAIL = "RAIL"
    BUS = "BUS"
    FERRY = "FERRY"


class Leg(BaseModel):
    """A single segment of a journey."""

    mode: TransportMode
    start: datetime
    end: datetime
    duration: int = Field(..., description="Duration in seconds")
    distance: float = Field(..., description="Distance in meters")
    from_place: Place
    to_place: Place


class Itinerary(BaseModel):
    """A complete journey from origin to destination."""

    start: datetime
    end: datetime
    duration: int = Field(..., description="Total duration in seconds")
    walk_distance: float = Field(..., description="Total walking distance in meters")
    walk_time: int = Field(..., description="Total walking time in seconds")
    legs: List[Leg]
