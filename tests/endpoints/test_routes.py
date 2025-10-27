"""
Unit tests for routes endpoint.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.schemas.geo import Coordinates
from app.schemas.itinary import Itinerary, Leg, Route, TransportMode
from app.schemas.location import Place
from app.services.routing_service import RoutingAPIError, RoutingDataError, RoutingNetworkError


@pytest.fixture
def sample_itineraries():
    """Create sample itineraries for testing."""
    return [
        Itinerary(
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
    ]


@pytest.fixture
def sample_itineraries_with_insights():
    """Create sample itineraries with AI insights for testing."""
    return [
        Itinerary(
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
                    ai_insight=(
                        "Short walk to the bus stop. "
                        "The route is well-lit and pedestrian-friendly."
                    ),
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
                    ai_insight=(
                        "Express bus with comfortable seats. "
                        "Usually not crowded at this time."
                    ),
                ),
            ],
        )
    ]


def test_search_routes_success(client: TestClient, sample_itineraries):
    """Test successful route search."""
    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": {"latitude": 60.1699, "longitude": 24.9384},
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
                "num_itineraries": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "origin" in data
        assert "destination" in data
        assert "itineraries" in data
        assert "search_time" in data
        # ai_description is optional, may or may not be present

        # Verify origin and destination
        assert data["origin"]["latitude"] == 60.1699
        assert data["origin"]["longitude"] == 24.9384
        assert data["destination"]["latitude"] == 60.2055
        assert data["destination"]["longitude"] == 24.6559

        # Verify itineraries
        assert len(data["itineraries"]) == 1
        itinerary = data["itineraries"][0]
        assert itinerary["duration"] == 2700
        assert itinerary["walk_distance"] == 500.0
        assert len(itinerary["legs"]) == 2


def test_search_routes_with_earliest_departure(client: TestClient, sample_itineraries):
    """Test route search with custom earliest departure time."""
    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": {"latitude": 60.1699, "longitude": 24.9384},
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
                "earliest_departure": "2025-10-14T12:00:00Z",
            },
        )

        assert response.status_code == 200
        # Verify the service was called
        mock_service.get_itinaries.assert_called_once()


def test_search_routes_default_num_itineraries(client: TestClient, sample_itineraries):
    """Test that num_itineraries defaults to 3."""
    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": {"latitude": 60.1699, "longitude": 24.9384},
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
            },
        )

        assert response.status_code == 200
        # Verify service was called with default value
        call_args = mock_service.get_itinaries.call_args
        assert call_args.kwargs["first"] == 3


def test_search_routes_invalid_coordinates(client: TestClient):
    """Test route search with invalid coordinates."""
    response = client.post(
        "/api/v1/routes/search",
        json={
            "origin": {"latitude": 91.0, "longitude": 24.9384},  # Invalid latitude
            "destination": {"latitude": 60.2055, "longitude": 24.6559},
        },
    )

    assert response.status_code == 422  # Validation error


def test_search_routes_missing_origin(client: TestClient):
    """Test route search with missing origin."""
    response = client.post(
        "/api/v1/routes/search",
        json={
            "destination": {"latitude": 60.2055, "longitude": 24.6559},
        },
    )

    assert response.status_code == 422


def test_search_routes_missing_destination(client: TestClient):
    """Test route search with missing destination."""
    response = client.post(
        "/api/v1/routes/search",
        json={
            "origin": {"latitude": 60.1699, "longitude": 24.9384},
        },
    )

    assert response.status_code == 422


def test_search_routes_invalid_num_itineraries_too_low(client: TestClient):
    """Test route search with num_itineraries below minimum."""
    response = client.post(
        "/api/v1/routes/search",
        json={
            "origin": {"latitude": 60.1699, "longitude": 24.9384},
            "destination": {"latitude": 60.2055, "longitude": 24.6559},
            "num_itineraries": 0,  # Below minimum of 1
        },
    )

    assert response.status_code == 422


def test_search_routes_invalid_num_itineraries_too_high(client: TestClient):
    """Test route search with num_itineraries above maximum."""
    response = client.post(
        "/api/v1/routes/search",
        json={
            "origin": {"latitude": 60.1699, "longitude": 24.9384},
            "destination": {"latitude": 60.2055, "longitude": 24.6559},
            "num_itineraries": 11,  # Above maximum of 10
        },
    )

    assert response.status_code == 422


def test_search_routes_hsl_api_error(client: TestClient):
    """Test handling of HSL API errors."""
    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(side_effect=RoutingAPIError("API error"))

        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": {"latitude": 60.1699, "longitude": 24.9384},
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
            },
        )

        assert response.status_code == 502
        assert "HSL API error" in response.json()["detail"]


def test_search_routes_network_error(client: TestClient):
    """Test handling of network errors."""
    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(side_effect=RoutingNetworkError("Network error"))

        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": {"latitude": 60.1699, "longitude": 24.9384},
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
            },
        )

        assert response.status_code == 503
        assert "Network error" in response.json()["detail"]


def test_search_routes_data_error(client: TestClient):
    """Test handling of data parsing errors."""
    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(side_effect=RoutingDataError("Parse error"))

        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": {"latitude": 60.1699, "longitude": 24.9384},
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
            },
        )

        assert response.status_code == 502
        assert "Failed to parse" in response.json()["detail"]


def test_search_routes_empty_result(client: TestClient):
    """Test route search with no results."""
    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(return_value=[])

        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": {"latitude": 60.1699, "longitude": 24.9384},
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["itineraries"]) == 0


def test_search_routes_coordinates_validation(client: TestClient):
    """Test coordinate validation with various invalid values."""
    test_cases = [
        {"latitude": -91.0, "longitude": 0.0},  # Latitude too low
        {"latitude": 91.0, "longitude": 0.0},  # Latitude too high
        {"latitude": 0.0, "longitude": -181.0},  # Longitude too low
        {"latitude": 0.0, "longitude": 181.0},  # Longitude too high
    ]

    for invalid_coords in test_cases:
        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": invalid_coords,
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
            },
        )
        assert response.status_code == 422


def test_search_routes_valid_edge_coordinates(client: TestClient, sample_itineraries):
    """Test route search with edge case valid coordinates."""
    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

        # Test edge cases that should be valid
        edge_cases = [
            {"latitude": -90.0, "longitude": -180.0},  # Min values
            {"latitude": 90.0, "longitude": 180.0},  # Max values
            {"latitude": 0.0, "longitude": 0.0},  # Zero values
        ]

        for coords in edge_cases:
            response = client.post(
                "/api/v1/routes/search",
                json={
                    "origin": coords,
                    "destination": {"latitude": 60.2055, "longitude": 24.6559},
                },
            )
            assert response.status_code == 200


def test_search_routes_without_ai_description(client: TestClient, sample_itineraries):
    """Test that route response works without ai_description (graceful degradation)."""
    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": {"latitude": 60.1699, "longitude": 24.9384},
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify ai_description is present but can be None
        assert "ai_description" in data
        # When not provided, it should be None
        assert data["ai_description"] is None


def test_search_routes_with_ai_description(client: TestClient, sample_itineraries):
    """Test that route response validates correctly when ai_description is provided."""
    # Test the schema validation directly
    from app.schemas.geo import Coordinates
    from app.schemas.routes import RouteSearchResponse

    # Schema should validate with ai_description
    response_data = RouteSearchResponse(
        origin=Coordinates(latitude=60.1699, longitude=24.9384),
        destination=Coordinates(latitude=60.2055, longitude=24.6559),
        itineraries=sample_itineraries,
        search_time=datetime.now(timezone.utc),
        ai_description="This route offers multiple options with varying travel times.",
    )
    assert (
        response_data.ai_description
        == "This route offers multiple options with varying travel times."
    )

    # Schema should validate without ai_description
    response_data_no_ai = RouteSearchResponse(
        origin=Coordinates(latitude=60.1699, longitude=24.9384),
        destination=Coordinates(latitude=60.2055, longitude=24.6559),
        itineraries=sample_itineraries,
        search_time=datetime.now(timezone.utc),
    )
    assert response_data_no_ai.ai_description is None


def test_search_routes_with_ai_insights_success(client: TestClient, sample_itineraries):
    """Test successful route search with AI insights for each leg."""
    with patch("app.api.v1.endpoints.routes.routing_service") as mock_routing_service:
        with patch("app.api.v1.endpoints.routes.ai_agents_service") as mock_ai_service:
            mock_routing_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

            # Mock AI service to return insights
            async def mock_get_insight(leg):
                if leg.mode == TransportMode.WALK:
                    return "Short walk to the bus stop."
                return "Express bus with comfortable seats."

            mock_ai_service.get_route_insight = AsyncMock(side_effect=mock_get_insight)

            response = client.post(
                "/api/v1/routes/search",
                json={
                    "origin": {"latitude": 60.1699, "longitude": 24.9384},
                    "destination": {"latitude": 60.2055, "longitude": 24.6559},
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Verify AI insights are present in legs
            assert len(data["itineraries"]) == 1
            itinerary = data["itineraries"][0]
            assert len(itinerary["legs"]) == 2

            # Check first leg (WALK)
            assert itinerary["legs"][0]["ai_insight"] == "Short walk to the bus stop."

            # Check second leg (BUS)
            assert itinerary["legs"][1]["ai_insight"] == "Express bus with comfortable seats."

            # Verify AI service was called for each leg
            assert mock_ai_service.get_route_insight.call_count == 2


def test_search_routes_with_ai_service_unavailable(client: TestClient, sample_itineraries):
    """Test graceful degradation when AI service is unavailable."""
    with patch("app.api.v1.endpoints.routes.routing_service") as mock_routing_service:
        with patch("app.api.v1.endpoints.routes.ai_agents_service") as mock_ai_service:
            mock_routing_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

            # Mock AI service to return None (service unavailable)
            mock_ai_service.get_route_insight = AsyncMock(return_value=None)

            response = client.post(
                "/api/v1/routes/search",
                json={
                    "origin": {"latitude": 60.1699, "longitude": 24.9384},
                    "destination": {"latitude": 60.2055, "longitude": 24.6559},
                },
            )

            # Should still succeed with 200, but without AI insights
            assert response.status_code == 200
            data = response.json()

            # Verify response structure is intact
            assert len(data["itineraries"]) == 1
            itinerary = data["itineraries"][0]
            assert len(itinerary["legs"]) == 2

            # AI insights should be None
            assert itinerary["legs"][0]["ai_insight"] is None
            assert itinerary["legs"][1]["ai_insight"] is None


def test_search_routes_with_ai_service_partial_failure(client: TestClient, sample_itineraries):
    """Test graceful degradation when AI service fails for some legs."""
    with patch("app.api.v1.endpoints.routes.routing_service") as mock_routing_service:
        with patch("app.api.v1.endpoints.routes.ai_agents_service") as mock_ai_service:
            mock_routing_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

            # Mock AI service to succeed for first leg, fail for second
            call_count = 0

            async def mock_get_insight_partial(leg):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return "Short walk to the bus stop."
                return None  # Simulate failure for second leg

            mock_ai_service.get_route_insight = AsyncMock(side_effect=mock_get_insight_partial)

            response = client.post(
                "/api/v1/routes/search",
                json={
                    "origin": {"latitude": 60.1699, "longitude": 24.9384},
                    "destination": {"latitude": 60.2055, "longitude": 24.6559},
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Verify first leg has insight
            assert data["itineraries"][0]["legs"][0]["ai_insight"] == "Short walk to the bus stop."

            # Verify second leg has no insight (graceful degradation)
            assert data["itineraries"][0]["legs"][1]["ai_insight"] is None


def test_search_routes_with_ai_service_exception(client: TestClient, sample_itineraries):
    """Test graceful degradation when AI service raises an exception."""
    with patch("app.api.v1.endpoints.routes.routing_service") as mock_routing_service:
        with patch("app.api.v1.endpoints.routes.ai_agents_service") as mock_ai_service:
            mock_routing_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

            # Mock AI service to raise an exception
            mock_ai_service.get_route_insight = AsyncMock(side_effect=Exception("AI service error"))

            response = client.post(
                "/api/v1/routes/search",
                json={
                    "origin": {"latitude": 60.1699, "longitude": 24.9384},
                    "destination": {"latitude": 60.2055, "longitude": 24.6559},
                },
            )

            # Should still succeed with 200, gracefully degrading
            assert response.status_code == 200
            data = response.json()

            # Verify response structure is intact
            assert len(data["itineraries"]) == 1
            itinerary = data["itineraries"][0]
            assert len(itinerary["legs"]) == 2

            # AI insights should be None due to graceful degradation
            assert itinerary["legs"][0]["ai_insight"] is None
            assert itinerary["legs"][1]["ai_insight"] is None


def test_leg_schema_with_ai_insight():
    """Test that Leg schema correctly handles ai_insight field."""
    # Test leg with ai_insight
    leg_with_insight = Leg(
        mode=TransportMode.BUS,
        start=datetime(2025, 10, 14, 10, 0, 0, tzinfo=timezone.utc),
        end=datetime(2025, 10, 14, 10, 30, 0, tzinfo=timezone.utc),
        duration=1800,
        distance=10000.0,
        from_place=Place(
            coordinates=Coordinates(latitude=60.1699, longitude=24.9384),
            name="Start",
        ),
        to_place=Place(
            coordinates=Coordinates(latitude=60.2055, longitude=24.6559),
            name="End",
        ),
        route=Route(
            short_name="550",
            long_name="Helsinki - Espoo",
            description="Express bus service",
        ),
        ai_insight="This is an AI-generated insight about the leg.",
    )
    assert leg_with_insight.ai_insight == "This is an AI-generated insight about the leg."

    # Test leg without ai_insight
    leg_without_insight = Leg(
        mode=TransportMode.WALK,
        start=datetime(2025, 10, 14, 10, 0, 0, tzinfo=timezone.utc),
        end=datetime(2025, 10, 14, 10, 10, 0, tzinfo=timezone.utc),
        duration=600,
        distance=500.0,
        from_place=Place(
            coordinates=Coordinates(latitude=60.1699, longitude=24.9384),
            name="Start",
        ),
        to_place=Place(
            coordinates=Coordinates(latitude=60.1710, longitude=24.9400),
            name="End",
        ),
    )
    assert leg_without_insight.ai_insight is None
