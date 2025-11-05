import logging
from typing import Any, Optional

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.schemas.health import ServiceHealth
from app.schemas.insight import ItineraryInsight, ItineraryWithInsight, LegWithInsight
from app.schemas.itinary import Itinerary

logger = logging.getLogger(__name__)


class ItinerariesInsightRequest(BaseModel):
    itineraries: list[Itinerary]
    user_preferences: list[Any] | None = None


class ItinerariesInsightResponse(BaseModel):
    itinerary_insights: list[ItineraryInsight]


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

    async def get_itineraries_with_insights(
        self, itineraries: list[Itinerary], user_preferences: Optional[list] = None
    ) -> list[ItineraryWithInsight]:
        """
        Takes itineraries and returns AI-generated insights for each leg and each itineraries.
        """
        try:
            client = self._get_client()

            # Prepare request payload with itinerary information
            request_data = ItinerariesInsightRequest(
                itineraries=itineraries,
                user_preferences=user_preferences,
            )

            response = await client.post(
                "/insight/itineraries",
                json=request_data.model_dump(exclude_none=True),
            )

            if response.status_code == 200:
                response_data = ItinerariesInsightResponse(**response.json())

                return self._parse_itineraries_with_insights(
                    itineraries,
                    response_data.itinerary_insights,
                )

            logger.warning(
                "AI agents service returned non-200 status for itinerary insight: %s",
                response.status_code,
            )
        except httpx.TimeoutException:
            logger.warning("AI agents service request timed out for itinerary insight")
            return []
        except Exception as e:  # pylint: disable=broad-except
            logger.warning("Failed to get AI itinerary insight: %s", str(e))

        return []

    def _parse_itineraries_with_insights(
        self,
        itineraries: list[Itinerary],
        itinerary_insights: list[ItineraryInsight],
    ) -> list[ItineraryWithInsight]:
        """
        Combine itineraries with their corresponding AI-generated insights.
        """
        itineraries_with_insights = []
        for itinerary, itinerary_insight in zip(itineraries, itinerary_insights):
            itineraries_with_insights.append(
                self._parse_itinerary_with_insight(itinerary, itinerary_insight)
            )
        return itineraries_with_insights

    def _parse_itinerary_with_insight(
        self,
        itinerary: Itinerary,
        itinerary_insight: ItineraryInsight,
    ) -> ItineraryWithInsight:
        """
        Combine itinerary data with AI-generated insights into a single object.
        """
        legs_with_insights = []
        for leg, leg_insight in zip(itinerary.legs, itinerary_insight.leg_insights):
            legs_with_insights.append(
                LegWithInsight(**leg.model_dump(), ai_insight=leg_insight.ai_insight)
            )

        return ItineraryWithInsight(
            **itinerary.model_dump(),
            ai_insight=itinerary_insight.ai_insight,
            legs=legs_with_insights,
        )


# Singleton instance for dependency injection
ai_agents_service = AiAgentsService()
