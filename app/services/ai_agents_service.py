import logging
from typing import Optional

import httpx

from app.core.config import settings
from app.schemas.health import ServiceHealth
from app.schemas.itinary import Leg

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

    async def get_leg_insight(self, leg: Leg) -> Optional[str]:
        """
        Get AI-generated insight for a specific leg of the journey.

        Args:
            leg: The leg object containing journey segment information

        Returns:
            Optional[str]: AI-generated insight text, or None if unavailable

        Raises:
            No exceptions - gracefully degrades by returning None on errors
        """
        try:
            client = self._get_client()

            # Prepare request payload with leg information
            payload: dict[str, str | int | float | dict[str, str] | None] = {
                "mode": leg.mode.value,
                "duration": leg.duration,
                "distance": leg.distance,
                "from_place": leg.from_place.name,
                "to_place": leg.to_place.name,
            }

            # Include route information if available (e.g., bus number)
            if leg.route:
                payload["route"] = {
                    "short_name": leg.route.short_name,
                    "long_name": leg.route.long_name,
                }

            response = await client.post("/api/v1/insight/leg", json=payload)

            if response.status_code == 200:
                data = response.json()
                return data.get("insight")

            logger.warning("AI agents service returned non-200 status: %s", response.status_code)
            return None

        except httpx.TimeoutException:
            logger.warning("AI agents service request timed out")
            return None
        except Exception as e:  # pylint: disable=broad-except
            logger.warning("Failed to get AI insight: %s", str(e))
            return None

    async def get_itinerary_insight(self, itinerary) -> Optional[str]:
        """
        Get AI-generated description for a complete itinerary.

        Args:
            itinerary: The itinerary object containing complete journey information

        Returns:
            Optional[str]: AI-generated description text, or None if unavailable

        Raises:
            No exceptions - gracefully degrades by returning None on errors
        """
        try:
            client = self._get_client()

            # Prepare request payload with itinerary information
            payload = {
                "duration": itinerary.duration,
                "walk_distance": itinerary.walk_distance,
                "walk_time": itinerary.walk_time,
                "legs": [
                    {
                        "mode": leg.mode.value,
                        "duration": leg.duration,
                        "distance": leg.distance,
                        "from_place": leg.from_place.name,
                        "to_place": leg.to_place.name,
                        "route": (
                            {
                                "short_name": leg.route.short_name,
                                "long_name": leg.route.long_name,
                            }
                            if leg.route
                            else None
                        ),
                    }
                    for leg in itinerary.legs
                ],
            }

            response = await client.post("/api/v1/insight/itinerary", json=payload)

            if response.status_code == 200:
                data = response.json()
                return data.get("insight")

            logger.warning(
                "AI agents service returned non-200 status for itinerary: %s",
                response.status_code,
            )
            return None

        except httpx.TimeoutException:
            logger.warning("AI agents service request timed out for itinerary")
            return None
        except Exception as e:  # pylint: disable=broad-except
            logger.warning("Failed to get AI itinerary insight: %s", str(e))
            return None


# Singleton instance for dependency injection
ai_agents_service = AiAgentsService()
