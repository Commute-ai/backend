"""
Route Search Request/Response Schemas

Pydantic models for route search API endpoint.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.geo import Coordinates
from app.schemas.itinary import Itinerary


class RouteSearchRequest(BaseModel):
    """Request schema for route search endpoint."""

    origin: Coordinates = Field(..., description="Starting location coordinates")
    destination: Coordinates = Field(..., description="Destination location coordinates")
    earliest_departure: Optional[datetime] = Field(
        None,
        description=(
            "Earliest departure time (ISO format). " "Defaults to current time if not provided."
        ),
    )
    num_itineraries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of route alternatives to return (1-10, default: 3)",
    )


class RouteSearchResponse(BaseModel):
    """Response schema for route search endpoint."""

    origin: Coordinates
    destination: Coordinates
    itineraries: List[Itinerary] = Field(..., description="List of route itineraries")
    search_time: datetime = Field(..., description="Time when the search was performed")
    ai_description: Optional[str] = Field(
        None, description="AI-generated description of the route options"
    )
