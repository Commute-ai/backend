"""
AI Agents Service Schemas

Pydantic models for AI Agents API request and response data.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.itinary import Itinerary
from app.schemas.preference import PreferenceBase


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
    """Request schema for AI itinerary insight endpoint (single itinerary)."""

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
    """Response schema for AI itinerary insight endpoint (single itinerary)."""

    ai_description: Optional[str] = Field(
        None, description="AI-generated description of the overall itinerary"
    )
    ai_insights: List[Optional[str]] = Field(
        default_factory=list, description="List of AI-generated insights for each leg"
    )


# New schemas for batch itineraries endpoint


class LegInsight(BaseModel):
    """Insight for a single leg of an itinerary."""

    ai_insight: str = Field(..., description="AI-generated insight for this leg")


class ItineraryInsight(BaseModel):
    """Insight for a complete itinerary."""

    ai_insight: str = Field(..., description="AI-generated insight for the overall itinerary")
    leg_insights: List[LegInsight] = Field(..., description="List of insights for each leg")


class ItineraryInsightsRequest(BaseModel):
    """Request schema for batch itineraries insights endpoint."""

    itineraries: List[Itinerary] = Field(..., description="List of itineraries to analyze")
    user_preferences: List[PreferenceBase] = Field(
        ..., description="User preferences to consider for insights"
    )


class ItineraryInsightsResponse(BaseModel):
    """Response schema for batch itineraries insights endpoint."""

    itenerary_insights: List[ItineraryInsight] = Field(
        ..., description="List of insights for each itinerary"
    )
