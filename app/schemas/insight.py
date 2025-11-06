from pydantic import BaseModel, Field

from app.schemas.itinary import Itinerary, Leg


class LegInsight(BaseModel):
    """Insight information for a single leg of the itinerary."""

    ai_insight: str = Field(
        ..., description="AI-generated insight about the leg"
    )


class ItineraryInsight(BaseModel):
    """Insight information for a given itinerary."""

    ai_insight: str = Field(
        ..., description="AI-generated insight about the itinerary"
    )
    leg_insights: list[LegInsight] = Field(
        ..., description="List of insights for each leg"
    )


class LegWithInsight(Leg):
    """A single segment of a journey with AI insight."""

    ai_insight: str = Field(
        ..., description="AI-generated insight about the leg"
    )


class ItineraryWithInsight(Itinerary):
    """A complete journey from origin to destination with AI insights."""

    ai_insight: str = Field(
        ..., description="AI-generated insight about the itinerary"
    )
    legs: list[LegWithInsight]  # type: ignore
