import logging
from typing import List, Optional

import httpx

from app.core.config import settings
from app.schemas.ai_agents import (
    ItineraryInsightRequest,
    ItineraryInsightResponse,
    ItineraryInsightsRequest,
    ItineraryInsightsResponse,
    LegInsightData,
    RouteInsightData,
)
from app.schemas.health import ServiceHealth
from app.schemas.itinary import Itinerary
from app.schemas.preference import PreferenceBase

logger = logging.getLogger(__name__)


class AiAgentsService:
    """
    Service for interacting with the AI Agents API.
    """

    def __init__(self):
        """
        Initialize the AI Agents service with configuration.
        """
        self._api_url = settings.AI_AGENTS_API_URL
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """
        Get or create the HTTP client for AI Agents API.

        Returns:
            httpx.AsyncClient instance for making requests to the AI Agents API.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self._api_url, timeout=10.0)
        return self._client

    async def health_check(self) -> ServiceHealth:
        """
        Perform a health check of the AI Agents service

        Returns:
            ServiceHealth indicating the health status of the AI Agents service.
        """
        try:
            client = self._get_client()
            response = await client.get("/health")

            if response.status_code == 200:
                return ServiceHealth(
                    healthy=True,
                    message="AI-agents API is responding",
                )
            return ServiceHealth(
                healthy=False,
                message=f"AI-agents API returned status code: {response.status_code}",
            )

        except httpx.TimeoutException:
            return ServiceHealth(
                healthy=False,
                message="AI-agents API request timed out",
            )
        except Exception as e:  # pylint: disable=broad-except
            return ServiceHealth(
                healthy=False,
                message=f"AI-agents API check failed: {str(e)}",
            )

    async def get_itinerary_insight(
        self, itinerary: Itinerary, user_preferences: Optional[list] = None
    ) -> None:
        """
        Get AI-generated insights for a complete itinerary and enrich it with AI data.

        This method sends the entire itinerary to the AI service and receives back:
        - ai_description: Overall description of the itinerary
        - ai_insights: List of insights for each leg

        The method directly modifies the itinerary object in place, setting:
        - itinerary.ai_description
        - leg.ai_insight for each leg

        Args:
            itinerary: The itinerary object containing the complete journey information
            user_preferences: Optional list of user preference strings to consider

        Returns:
            None - modifies the itinerary object in place

        Raises:
            No exceptions - gracefully degrades by returning without modification on errors
        """
        try:
            client = self._get_client()

            # Prepare request payload with itinerary information
            request_data = ItineraryInsightRequest(
                start=itinerary.start.isoformat(),
                end=itinerary.end.isoformat(),
                duration=itinerary.duration,
                walk_distance=itinerary.walk_distance,
                walk_time=itinerary.walk_time,
                legs=[
                    LegInsightData(
                        mode=leg.mode.value,
                        duration=leg.duration,
                        distance=leg.distance,
                        from_place=leg.from_place.name or "",
                        to_place=leg.to_place.name or "",
                        route=(
                            RouteInsightData(
                                short_name=leg.route.short_name,
                                long_name=leg.route.long_name,
                            )
                            if leg.route
                            else None
                        ),
                    )
                    for leg in itinerary.legs
                ],
                user_preferences=user_preferences,
            )

            response = await client.post(
                "/api/v1/insight/itinerary", json=request_data.model_dump(exclude_none=True)
            )

            if response.status_code == 200:
                response_data = ItineraryInsightResponse(**response.json())

                # Set the itinerary-level AI description
                itinerary.ai_description = response_data.ai_description

                # Set AI insights for each leg
                for idx, leg in enumerate(itinerary.legs):
                    if idx < len(response_data.ai_insights):
                        leg.ai_insight = response_data.ai_insights[idx]
                    else:
                        leg.ai_insight = None

                return

            logger.warning(
                "AI agents service returned non-200 status for itinerary insight: %s",
                response.status_code,
            )

        except httpx.TimeoutException:
            logger.warning("AI agents service request timed out for itinerary insight")
        except Exception as e:  # pylint: disable=broad-except
            logger.warning("Failed to get AI itinerary insight: %s", str(e))

    async def get_itineraries_insights(
        self, itineraries: List[Itinerary], user_preferences: List[PreferenceBase]
    ) -> ItineraryInsightsResponse:
        """
        Get AI-generated insights for multiple itineraries.

        This method sends multiple itineraries to the AI service and receives back
        insights for each itinerary and their constituent legs.

        Args:
            itineraries: List of itinerary objects to analyze
            user_preferences: List of user preference objects to consider

        Returns:
            ItineraryInsightsResponse containing insights for all itineraries

        Raises:
            Exception: Raises exceptions on failure for proper error handling
        """
        try:
            client = self._get_client()

            # Prepare request payload with itineraries information
            request_data = ItineraryInsightsRequest(
                itineraries=itineraries,
                user_preferences=user_preferences,
            )

            response = await client.post(
                "/api/v1/insight/iteneraries", json=request_data.model_dump(mode="json")
            )

            if response.status_code == 200:
                response_data = ItineraryInsightsResponse(**response.json())
                return response_data

            logger.error(
                "AI agents service returned non-200 status for itineraries insights: %s",
                response.status_code,
            )
            raise Exception(f"AI agents service returned status {response.status_code}")

        except httpx.TimeoutException as e:
            logger.error("AI agents service request timed out for itineraries insights")
            raise Exception("AI agents service request timed out") from e
        except Exception as e:
            logger.error("Failed to get AI itineraries insights: %s", str(e))
            raise


# Singleton instance for dependency injection
ai_agents_service = AiAgentsService()
