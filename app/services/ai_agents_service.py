import logging
from typing import Optional

import httpx

from app.core.config import settings
from app.schemas.health import ServiceHealth

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


# Singleton instance for dependency injection
ai_agents_service = AiAgentsService()
