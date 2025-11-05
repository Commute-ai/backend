"""
AI Agents Service Schemas

Pydantic models for AI Agents API request and response data.
"""

from typing import List

from pydantic import BaseModel, Field

from app.schemas.itinary import Itinerary
from app.schemas.preference import PreferenceBase


class LegInsight(BaseModel):
    """Insight for a single leg of an itinerary."""

    ai_insight: str = Field(..., description="AI-generated insight for this leg")


class ItineraryInsight(BaseModel):
    """Insight for a complete itinerary."""

    ai_insight: str = Field(..., description="AI-generated insight for the overall itinerary")
    leg_insights: List[LegInsight] = Field(..., description="List of insights for each leg")


class ItineraryInsightRequest(BaseModel):
    """Request schema for AI itinerary insight endpoint."""

    itineraries: List[Itinerary] = Field(..., description="List of itineraries to analyze")
    user_preferences: List[PreferenceBase] = Field(
        ..., description="User preferences to consider for insights"
    )


class ItineraryInsightResponse(BaseModel):
    """Response schema for AI itinerary insight endpoint."""

    itenerary_insights: List[ItineraryInsight] = Field(
        ..., description="List of insights for each itinerary"
    )
