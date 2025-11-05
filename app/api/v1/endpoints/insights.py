"""
Insights API Endpoint

Provides REST API for getting AI-generated insights on itineraries.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.ai_agents import ItineraryInsightsRequest, ItineraryInsightsResponse
from app.services.ai_agents_service import ai_agents_service
from app.services.auth_service import auth_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/iteneraries", response_model=ItineraryInsightsResponse)
async def get_itineraries_insights(
    request: ItineraryInsightsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
) -> Any:
    """
    Get AI-generated insights for multiple itineraries.

    Analyzes multiple itineraries and provides AI-generated insights for each
    itinerary and their constituent legs based on user preferences.

    Args:
        request: Request containing itineraries and user preferences
        db: Database session
        current_user: Authenticated user (required)

    Returns:
        ItineraryInsightsResponse with insights for each itinerary

    Raises:
        HTTPException: If the insights generation fails
    """
    logger.info(
        "Itineraries insights request: num_itineraries=%s, num_preferences=%s, user_id=%s",
        len(request.itineraries),
        len(request.user_preferences),
        current_user.id,
    )

    try:
        # Get insights from AI agents service
        insights = await ai_agents_service.get_itineraries_insights(
            request.itineraries, request.user_preferences
        )

        logger.info(
            "Itineraries insights successful: generated %d insights",
            len(insights.itenerary_insights),
        )

        return insights

    except Exception as e:
        logger.exception("Unexpected error in itineraries insights")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating insights",
        ) from e
