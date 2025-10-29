"""
Routes API Endpoint

Provides REST API for querying HSL public transport routes.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas.routes import RouteSearchRequest, RouteSearchResponse
from app.services.ai_agents_service import ai_agents_service
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
async def search_routes(request: RouteSearchRequest) -> Any:
    """
    Search for public transport routes between two locations.

    Queries the HSL (Helsinki Regional Transport) API to find route alternatives
    between origin and destination coordinates.

    Args:
        request: Route search parameters including origin, destination, and preferences

    Returns:
        RouteSearchResponse with list of available route itineraries

    Raises:
        HTTPException: If the route search fails or returns invalid data
    """
    logger.info(
        "Route search request: origin=%s, destination=%s, num_itineraries=%s",
        request.origin,
        request.destination,
        request.num_itineraries,
    )

    # Use current time if earliest_departure not provided
    earliest_departure = request.earliest_departure or datetime.now(timezone.utc)

    try:
        # Call routing service to fetch itineraries from HSL API
        itineraries = await routing_service.get_itinaries(
            origin=request.origin,
            destination=request.destination,
            earliest_departure=earliest_departure,
            first=request.num_itineraries,
        )

        # Enhance each itinerary with AI description and each leg with AI insights
        for itinerary in itineraries:
            # Get AI description for the complete itinerary (with graceful degradation)
            try:
                ai_description = await ai_agents_service.get_itinerary_insight(itinerary)
                itinerary.ai_description = ai_description
            except Exception as e:  # pylint: disable=broad-except
                # Gracefully degrade - log warning but continue without AI description
                logger.warning("Failed to get AI description for itinerary: %s", str(e))
                itinerary.ai_description = None

            # Get AI insights for each leg (with graceful degradation)
            for leg in itinerary.legs:
                try:
                    ai_insight = await ai_agents_service.get_leg_insight(leg)
                    leg.ai_insight = ai_insight
                except Exception as e:  # pylint: disable=broad-except
                    # Gracefully degrade - log warning but continue without AI insight
                    logger.warning("Failed to get AI insight for leg: %s", str(e))
                    leg.ai_insight = None

        logger.info("Route search successful: found %d itineraries", len(itineraries))

        return RouteSearchResponse(
            origin=request.origin,
            destination=request.destination,
            itineraries=itineraries,
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
