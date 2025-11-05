"""
Unit tests for AI agents service.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.schemas.geo import Coordinates
from app.schemas.itinary import Itinerary, Leg, Route, TransportMode
from app.schemas.location import Place
from app.services.ai_agents_service import AiAgentsService


@pytest.fixture
def ai_service():
    """Create an AI agents service instance for testing."""
    return AiAgentsService()


@pytest.fixture
def sample_leg():
    """Create a sample leg for testing."""
    return Leg(
        mode=TransportMode.BUS,
        start=datetime(2025, 10, 14, 10, 0, 0, tzinfo=timezone.utc),
        end=datetime(2025, 10, 14, 10, 30, 0, tzinfo=timezone.utc),
        duration=1800,
        distance=10000.0,
        from_place=Place(
            coordinates=Coordinates(latitude=60.1699, longitude=24.9384),
            name="Helsinki Central",
        ),
        to_place=Place(
            coordinates=Coordinates(latitude=60.2055, longitude=24.6559),
            name="Espoo Central",
        ),
        route=Route(
            short_name="550",
            long_name="Helsinki - Espoo",
            description="Express bus service",
        ),
    )


@pytest.fixture
def sample_walk_leg():
    """Create a sample walking leg for testing."""
    return Leg(
        mode=TransportMode.WALK,
        start=datetime(2025, 10, 14, 10, 0, 0, tzinfo=timezone.utc),
        end=datetime(2025, 10, 14, 10, 10, 0, tzinfo=timezone.utc),
        duration=600,
        distance=500.0,
        from_place=Place(
            coordinates=Coordinates(latitude=60.1699, longitude=24.9384),
            name="Origin",
        ),
        to_place=Place(
            coordinates=Coordinates(latitude=60.1710, longitude=24.9400),
            name="Bus Stop",
        ),
        route=None,
    )


@pytest.mark.asyncio
async def test_health_check_success(ai_service):
    """Test successful health check."""
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch.object(ai_service, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        health = await ai_service.health_check()

        assert health.healthy is True
        assert "responding" in health.message.lower()


@pytest.mark.asyncio
async def test_health_check_failure(ai_service):
    """Test health check with non-200 status."""
    mock_response = MagicMock()
    mock_response.status_code = 503

    with patch.object(ai_service, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        health = await ai_service.health_check()

        assert health.healthy is False
        assert "503" in health.message


@pytest.mark.asyncio
async def test_health_check_timeout(ai_service):
    """Test health check with timeout."""
    with patch.object(ai_service, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_get_client.return_value = mock_client

        health = await ai_service.health_check()

        assert health.healthy is False
        assert "timed out" in health.message.lower()


@pytest.mark.asyncio
async def test_health_check_exception(ai_service):
    """Test health check with exception."""
    with patch.object(ai_service, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection error"))
        mock_get_client.return_value = mock_client

        health = await ai_service.health_check()

        assert health.healthy is False
        assert "failed" in health.message.lower()


@pytest.fixture
def sample_itinerary():
    """Create a sample itinerary for testing."""
    return Itinerary(
        start=datetime(2025, 10, 14, 10, 0, 0, tzinfo=timezone.utc),
        end=datetime(2025, 10, 14, 10, 45, 0, tzinfo=timezone.utc),
        duration=2700,
        walk_distance=500.0,
        walk_time=400,
        legs=[
            Leg(
                mode=TransportMode.WALK,
                start=datetime(2025, 10, 14, 10, 0, 0, tzinfo=timezone.utc),
                end=datetime(2025, 10, 14, 10, 10, 0, tzinfo=timezone.utc),
                duration=600,
                distance=500.0,
                from_place=Place(
                    coordinates=Coordinates(latitude=60.1699, longitude=24.9384),
                    name="Origin",
                ),
                to_place=Place(
                    coordinates=Coordinates(latitude=60.1710, longitude=24.9400),
                    name="Bus Stop",
                ),
                route=None,
            ),
            Leg(
                mode=TransportMode.BUS,
                start=datetime(2025, 10, 14, 10, 10, 0, tzinfo=timezone.utc),
                end=datetime(2025, 10, 14, 10, 45, 0, tzinfo=timezone.utc),
                duration=2100,
                distance=15000.0,
                from_place=Place(
                    coordinates=Coordinates(latitude=60.1710, longitude=24.9400),
                    name="Bus Stop",
                ),
                to_place=Place(
                    coordinates=Coordinates(latitude=60.2055, longitude=24.6559),
                    name="Destination",
                ),
                route=Route(
                    short_name="550",
                    long_name="Helsinki - Espoo",
                    description="Express bus service",
                ),
            ),
        ],
    )
