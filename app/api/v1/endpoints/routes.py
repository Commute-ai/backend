"""
Routes API Endpoint

Provides REST API for querying HSL public transport routes.
"""

import logging
from datetime import datetime, timezone
from typing import List, cast

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.insight import ItineraryWithInsight
from app.schemas.itinary import Itinerary
from app.schemas.routes import RouteSearchRequest, RouteSearchResponse
from app.services.ai_agents_service import ai_agents_service
from app.services.auth_service import auth_service
from app.services.preference_service import preference_service
from app.services.routing_service import (
    RoutingAPIError,
    RoutingDataError,
    RoutingNetworkError,
    RoutingServiceError,
    routing_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search", response_model=RouteSearchResponse)
async def search_routes(
    request: RouteSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Search for public transport routes between two locations.

    Queries the HSL (Helsinki Regional Transport) API to find route alternatives
    between origin and destination coordinates. Requires authentication.

    Args:
        request: Route search parameters including origin, destination, and preferences
        db: Database session
        current_user: Authenticated user (required)

    Returns:
        RouteSearchResponse with list of available route itineraries

    Raises:
        HTTPException: If the route search fails or returns invalid data
    """
    logger.info(
        "Route search request: origin=%s, destination=%s, num_itineraries=%s, user_id=%s",
        request.origin,
        request.destination,
        request.num_itineraries,
        current_user.id,
    )

    # Use current time if earliest_departure not provided
    earliest_departure = request.earliest_departure or datetime.now(timezone.utc)

    # Collect user preferences from multiple sources
    user_preferences: List[str] = []

    # 1. Add preferences from request (explicitly provided)
    if request.preferences:
        user_preferences.extend(request.preferences)

    # 2. Add stored preferences from authenticated user
    try:
        stored_prefs = preference_service.get_user_preferences(db, int(current_user.id))
        user_preferences.extend([str(pref.prompt) for pref in stored_prefs])
    except Exception as e:  # pylint: disable=broad-except
        logger.warning("Failed to fetch user preferences: %s", str(e))

    logger.info("Using %d user preferences for route insights", len(user_preferences))

    try:
        # Call routing service to fetch itineraries from HSL API
        itineraries = await routing_service.get_itinaries(
            origin=request.origin,
            destination=request.destination,
            earliest_departure=earliest_departure,
            first=request.num_itineraries,
        )

        # Try to get AI insights for all itineraries
        try:
            itineraries_with_insights = await ai_agents_service.get_itineraries_with_insights(
                itineraries, user_preferences if user_preferences else None
            )
            final_itineraries = (
                cast(list[Itinerary | ItineraryWithInsight], itineraries_with_insights)
                if itineraries_with_insights
                else itineraries
            )

        except Exception as e:  # pylint: disable=broad-except
            # Gracefully degrade - log warning but continue without AI insights
            logger.warning("Failed to get AI insights for itinerary: %s", str(e))
            final_itineraries = itineraries

        logger.info("Route search successful: found %d itineraries", len(itineraries))

        return RouteSearchResponse(
            origin=request.origin,
            destination=request.destination,
            itineraries=final_itineraries,
            search_time=datetime.now(timezone.utc),
        )

    except RoutingAPIError as e:
        logger.error("HSL API error: %s", str(e))
        raise HTTPException(
            status_code=502,
            detail=f"HSL API error: {str(e)}",
        ) from e

    except RoutingNetworkError as e:
        logger.error("Network error: %s", str(e))
        raise HTTPException(
            status_code=503,
            detail=f"Network error connecting to HSL API: {str(e)}",
        ) from e

    except RoutingDataError as e:
        logger.error("Data parsing error: %s", str(e))
        raise HTTPException(
            status_code=502,
            detail=f"Failed to parse HSL API response: {str(e)}",
        ) from e

    except RoutingServiceError as e:
        logger.error("Routing service error: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Routing service error: {str(e)}",
        ) from e

    except Exception as e:
        logger.exception("Unexpected error in route search")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while searching for routes",
        ) from e
