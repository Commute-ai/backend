"""
Unit tests for routing service.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.geo import Coordinates
from app.schemas.itinary import Itinerary, Leg, Route, TransportMode
from app.services.routing_service import RoutingService


@pytest.fixture
def routing_service():
    """Create a routing service instance for testing."""
    return RoutingService()


@pytest.fixture
def sample_coordinates():
    """Sample coordinates for testing."""
    return {
        "origin": Coordinates(latitude=60.1699, longitude=24.9384),  # Helsinki
        "destination": Coordinates(latitude=60.2055, longitude=24.6559),  # Espoo
    }


@pytest.fixture
def sample_graphql_response():
    """Sample GraphQL API response."""
    return {
        "planConnection": {
            "edges": [
                {
                    "node": {
                        "start": "2025-10-14T10:00:00+03:00",
                        "end": "2025-10-14T10:45:00+03:00",
                        "duration": 2700,
                        "walkDistance": 500.0,
                        "walkTime": 400,
                        "legs": [
                            {
                                "mode": "WALK",
                                "start": {"scheduledTime": "2025-10-14T10:00:00+03:00"},
                                "end": {"scheduledTime": "2025-10-14T10:10:00+03:00"},
                                "duration": 600,
                                "distance": 500.0,
                                "from": {
                                    "name": "Origin",
                                    "lat": 60.1699,
                                    "lon": 24.9384,
                                },
                                "to": {
                                    "name": "Bus Stop",
                                    "lat": 60.1710,
                                    "lon": 24.9400,
                                },
                                "route": None,
                            },
                            {
                                "mode": "BUS",
                                "start": {"scheduledTime": "2025-10-14T10:10:00+03:00"},
                                "end": {"scheduledTime": "2025-10-14T10:45:00+03:00"},
                                "duration": 2100,
                                "distance": 15000.0,
                                "from": {
                                    "name": "Bus Stop",
                                    "lat": 60.1710,
                                    "lon": 24.9400,
                                },
                                "to": {
                                    "name": "Destination",
                                    "lat": 60.2055,
                                    "lon": 24.6559,
                                },
                                "route": {
                                    "shortName": "550",
                                    "longName": "Helsinki - Espoo",
                                    "desc": "Express bus service",
                                },
                            },
                        ],
                    }
                }
            ]
        }
    }


@pytest.mark.asyncio
async def test_get_itinaries_success(routing_service, sample_coordinates, sample_graphql_response):
    """Test successful itinerary fetch."""
    with patch.object(routing_service, "_get_client") as mock_client:
        mock_gql_client = MagicMock()
        mock_gql_client.execute_async = AsyncMock(return_value=sample_graphql_response)
        mock_client.return_value = mock_gql_client

        itineraries = await routing_service.get_itinaries(
            origin=sample_coordinates["origin"],
            destination=sample_coordinates["destination"],
        )

        assert len(itineraries) == 1
        assert isinstance(itineraries[0], Itinerary)
        assert itineraries[0].duration == 2700
        assert itineraries[0].walk_distance == 500.0
        assert len(itineraries[0].legs) == 2


@pytest.mark.asyncio
async def test_get_itinaries_with_custom_params(routing_service, sample_coordinates):
    """Test itinerary fetch with custom parameters."""
    departure_time = datetime(2025, 10, 14, 12, 0, 0, tzinfo=timezone.utc)

    with patch.object(routing_service, "_get_client") as mock_client:
        mock_gql_client = MagicMock()
        mock_gql_client.execute_async = AsyncMock(return_value={"planConnection": {"edges": []}})
        mock_client.return_value = mock_gql_client

        await routing_service.get_itinaries(
            origin=sample_coordinates["origin"],
            destination=sample_coordinates["destination"],
            earliest_departure=departure_time,
            first=5,
        )

        call_args = mock_gql_client.execute_async.call_args
        variables = call_args[1]["variable_values"]

        assert variables["first"] == 5
        assert variables["originLat"] == sample_coordinates["origin"].latitude
        assert variables["destinationLat"] == sample_coordinates["destination"].latitude


def test_parse_itinary(routing_service, sample_graphql_response):
    """Test parsing of itinerary data."""
    node = sample_graphql_response["planConnection"]["edges"][0]["node"]
    itinerary = routing_service._parse_itinary(node)

    assert isinstance(itinerary, Itinerary)
    assert itinerary.duration == 2700
    assert itinerary.walk_distance == 500.0
    assert itinerary.walk_time == 400
    assert len(itinerary.legs) == 2


def test_parse_leg_walk(routing_service):
    """Test parsing of walking leg."""
    leg_data = {
        "mode": "WALK",
        "start": {"scheduledTime": "2025-10-14T10:00:00+03:00"},
        "end": {"scheduledTime": "2025-10-14T10:10:00+03:00"},
        "duration": 600,
        "distance": 500.0,
        "from": {"name": "Start", "lat": 60.1699, "lon": 24.9384},
        "to": {"name": "End", "lat": 60.1710, "lon": 24.9400},
        "route": None,
    }

    leg = routing_service._parse_leg(leg_data)

    assert isinstance(leg, Leg)
    assert leg.mode == TransportMode.WALK
    assert leg.duration == 600
    assert leg.distance == 500.0
    assert leg.route is None
    assert leg.from_place.name == "Start"
    assert leg.to_place.name == "End"


def test_parse_leg_with_route(routing_service):
    """Test parsing of leg with route information."""
    leg_data = {
        "mode": "BUS",
        "start": {"scheduledTime": "2025-10-14T10:10:00+03:00"},
        "end": {"scheduledTime": "2025-10-14T10:45:00+03:00"},
        "duration": 2100,
        "distance": 15000.0,
        "from": {"name": "Bus Stop", "lat": 60.1710, "lon": 24.9400},
        "to": {"name": "Destination", "lat": 60.2055, "lon": 24.6559},
        "route": {
            "shortName": "550",
            "longName": "Helsinki - Espoo",
            "desc": "Express bus",
        },
    }

    leg = routing_service._parse_leg(leg_data)

    assert leg.mode == TransportMode.BUS
    assert leg.route is not None
    assert leg.route.short_name == "550"
    assert leg.route.long_name == "Helsinki - Espoo"


def test_parse_route(routing_service):
    """Test parsing of route data."""
    route_data = {
        "shortName": "550",
        "longName": "Helsinki - Espoo",
        "desc": "Express bus service",
    }

    route = routing_service._parse_route(route_data)

    assert isinstance(route, Route)
    assert route.short_name == "550"
    assert route.long_name == "Helsinki - Espoo"
    assert route.description == "Express bus service"


@pytest.mark.asyncio
async def test_get_itinaries_empty_response(routing_service, sample_coordinates):
    """Test handling of empty API response."""
    with patch.object(routing_service, "_get_client") as mock_client:
        mock_gql_client = MagicMock()
        mock_gql_client.execute_async = AsyncMock(return_value={"planConnection": {"edges": []}})
        mock_client.return_value = mock_gql_client

        itineraries = await routing_service.get_itinaries(
            origin=sample_coordinates["origin"],
            destination=sample_coordinates["destination"],
        )

        assert len(itineraries) == 0


@pytest.mark.asyncio
async def test_close_client(routing_service):
    """Test closing the GraphQL client."""
    mock_client = MagicMock()
    mock_client.close_async = AsyncMock()
    routing_service._client = mock_client

    await routing_service.close()

    mock_client.close_async.assert_called_once()
    assert routing_service._client is None
