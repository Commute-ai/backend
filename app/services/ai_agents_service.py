import logging
from typing import List, Optional

import httpx

from app.core.config import settings
from app.schemas.ai_agents import ItineraryInsightRequest, ItineraryInsightResponse
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
        Get AI-generated insights for a single itinerary and enrich it with AI data.

        This is a convenience method that wraps get_itineraries_insight for single itinerary.
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
            # Convert string preferences to PreferenceBase objects
            from app.schemas.preference import PreferenceBase

            prefs = (
                [PreferenceBase(prompt=pref) for pref in user_preferences]
                if user_preferences
                else []
            )

            # Call the batch API with a single itinerary
            await self.get_itineraries_insight([itinerary], prefs)

        except Exception as e:  # pylint: disable=broad-except
            logger.warning("Failed to get AI itinerary insight: %s", str(e))

    async def get_itineraries_insight(
        self, itineraries: List[Itinerary], user_preferences: List[PreferenceBase]
    ) -> None:
        """
        Get AI-generated insights for multiple itineraries and enrich them with AI data.

        This method sends multiple itineraries to the AI service and receives back
        insights for each itinerary and their constituent legs. It modifies the
        itinerary objects in place.

        Args:
            itineraries: List of itinerary objects to analyze
            user_preferences: List of user preference objects to consider

        Returns:
            None - modifies the itinerary objects in place

        Raises:
            No exceptions - gracefully degrades by returning without modification on errors
        """
        try:
            client = self._get_client()

            # Prepare request payload with itineraries information
            request_data = ItineraryInsightRequest(
                itineraries=itineraries,
                user_preferences=user_preferences,
            )

            response = await client.post(
                "/api/v1/insight/iteneraries", json=request_data.model_dump(mode="json")
            )

            if response.status_code == 200:
                response_data = ItineraryInsightResponse(**response.json())

                # Map insights back to itineraries
                for idx, itinerary in enumerate(itineraries):
                    if idx < len(response_data.itenerary_insights):
                        insight = response_data.itenerary_insights[idx]

                        # Set the itinerary-level AI insight
                        itinerary.ai_description = insight.ai_insight

                        # Set AI insights for each leg
                        for leg_idx, leg in enumerate(itinerary.legs):
                            if leg_idx < len(insight.leg_insights):
                                leg.ai_insight = insight.leg_insights[leg_idx].ai_insight
                            else:
                                leg.ai_insight = None
                    else:
                        # No insight returned for this itinerary
                        itinerary.ai_description = None
                        for leg in itinerary.legs:
                            leg.ai_insight = None

                return

            logger.warning(
                "AI agents service returned non-200 status for itineraries insight: %s",
                response.status_code,
            )

        except httpx.TimeoutException:
            logger.warning("AI agents service request timed out for itineraries insight")
        except Exception as e:  # pylint: disable=broad-except
            logger.warning("Failed to get AI itineraries insight: %s", str(e))


# Singleton instance for dependency injection
ai_agents_service = AiAgentsService()
