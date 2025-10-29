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


@pytest.mark.asyncio
async def test_get_itinerary_insight_success(ai_service, sample_itinerary):
    """Test successful AI itinerary and leg insight retrieval."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ai_description": "This route combines a short walk with a direct bus connection.",
        "ai_insights": ["Short walk to the bus stop.", "Express bus with comfortable seats."],
    }

    with patch.object(ai_service, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        await ai_service.get_itinerary_insight(sample_itinerary)

        mock_client.post.assert_called_once()

        # Verify the payload structure
        call_args = mock_client.post.call_args
        assert call_args.args[0] == "/api/v1/insight/itinerary"
        payload = call_args.kwargs["json"]
        assert payload["duration"] == 2700
        assert payload["walk_distance"] == 500.0
        assert payload["walk_time"] == 400
        assert len(payload["legs"]) == 2
        assert payload["legs"][0]["mode"] == "WALK"
        assert payload["legs"][1]["mode"] == "BUS"

        # Verify the itinerary was enriched
        assert (
            sample_itinerary.ai_description
            == "This route combines a short walk with a direct bus connection."
        )
        assert sample_itinerary.legs[0].ai_insight == "Short walk to the bus stop."
        assert sample_itinerary.legs[1].ai_insight == "Express bus with comfortable seats."


@pytest.mark.asyncio
async def test_get_itinerary_insight_non_200_response(ai_service, sample_itinerary):
    """Test handling of non-200 response for itinerary insight."""
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch.object(ai_service, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        await ai_service.get_itinerary_insight(sample_itinerary)

        # Itinerary should not be modified on error
        assert sample_itinerary.ai_description is None
        assert sample_itinerary.legs[0].ai_insight is None
        assert sample_itinerary.legs[1].ai_insight is None


@pytest.mark.asyncio
async def test_get_itinerary_insight_timeout(ai_service, sample_itinerary):
    """Test handling of timeout for itinerary insight."""
    with patch.object(ai_service, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_get_client.return_value = mock_client

        await ai_service.get_itinerary_insight(sample_itinerary)

        # Itinerary should not be modified on timeout
        assert sample_itinerary.ai_description is None
        assert sample_itinerary.legs[0].ai_insight is None


@pytest.mark.asyncio
async def test_get_itinerary_insight_network_error(ai_service, sample_itinerary):
    """Test handling of network errors for itinerary insight."""
    with patch.object(ai_service, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.RequestError("Network error"))
        mock_get_client.return_value = mock_client

        await ai_service.get_itinerary_insight(sample_itinerary)

        # Itinerary should not be modified on network error
        assert sample_itinerary.ai_description is None
        assert sample_itinerary.legs[0].ai_insight is None


@pytest.mark.asyncio
async def test_get_itinerary_insight_exception(ai_service, sample_itinerary):
    """Test handling of unexpected exceptions for itinerary insight."""
    with patch.object(ai_service, "_get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("Unexpected error"))
        mock_get_client.return_value = mock_client

        await ai_service.get_itinerary_insight(sample_itinerary)

        # Itinerary should not be modified on exception
        assert sample_itinerary.ai_description is None
        assert sample_itinerary.legs[0].ai_insight is None
