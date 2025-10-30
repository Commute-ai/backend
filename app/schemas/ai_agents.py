"""
AI Agents Service Schemas

Pydantic models for AI Agents API request and response data.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class RouteInsightData(BaseModel):
    """Route information for itinerary insight request."""

    short_name: str = Field(..., description="Short name of the route")
    long_name: str = Field(..., description="Long name of the route")


class LegInsightData(BaseModel):
    """Leg information for itinerary insight request."""

    mode: str = Field(..., description="Transport mode (e.g., WALK, BUS, TRAM)")
    duration: int = Field(..., description="Duration in seconds")
    distance: float = Field(..., description="Distance in meters")
    from_place: str = Field(
        ..., description="Name of the starting place (empty string if not available)"
    )
    to_place: str = Field(
        ..., description="Name of the destination place (empty string if not available)"
    )
    route: Optional[RouteInsightData] = Field(None, description="Route information if applicable")


class ItineraryInsightRequest(BaseModel):
    """Request schema for AI itinerary insight endpoint."""

    start: str = Field(..., description="Start time in ISO format")
    end: str = Field(..., description="End time in ISO format")
    duration: int = Field(..., description="Total duration in seconds")
    walk_distance: float = Field(..., description="Total walking distance in meters")
    walk_time: int = Field(..., description="Total walking time in seconds")
    legs: List[LegInsightData] = Field(..., description="List of journey legs")
    user_preferences: Optional[List[str]] = Field(
        None, description="User preferences to consider for insights"
    )


class ItineraryInsightResponse(BaseModel):
    """Response schema for AI itinerary insight endpoint."""

    ai_description: Optional[str] = Field(
        None, description="AI-generated description of the overall itinerary"
    )
    ai_insights: List[Optional[str]] = Field(
        default_factory=list, description="List of AI-generated insights for each leg"
    )
