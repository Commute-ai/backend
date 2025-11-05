"""
Unit tests for routes endpoint.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.geo import Coordinates
from app.schemas.itinary import Itinerary, Leg, Route, TransportMode
from app.schemas.location import Place
from app.services.auth_service import auth_service
from app.services.routing_service import RoutingAPIError, RoutingDataError, RoutingNetworkError


def create_test_user(db: Session, username: str = "testuser") -> User:
    """Helper function to create a test user"""
    user = User(
        username=username,
        hashed_password=auth_service.get_password_hash("testpassword"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_header(user_id: int) -> dict:
    """Helper function to generate authorization header with token"""
    token = auth_service.generate_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


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
                        "Express bus with comfortable seats. " "Usually not crowded at this time."
                    ),
                ),
            ],
        )
    ]


def test_search_routes_success(db: Session, client: TestClient, sample_itineraries):
    """Test successful route search."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": {"latitude": 60.1699, "longitude": 24.9384},
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
                "num_itineraries": 3,
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "origin" in data
        assert "destination" in data
        assert "itineraries" in data
        assert "search_time" in data
        # ai_insight is optional, may or may not be present

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


def test_search_routes_with_earliest_departure(db: Session, client: TestClient, sample_itineraries):
    """Test route search with custom earliest departure time."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": {"latitude": 60.1699, "longitude": 24.9384},
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
                "earliest_departure": "2025-10-14T12:00:00Z",
            },
            headers=headers,
        )

        assert response.status_code == 200
        # Verify the service was called
        mock_service.get_itinaries.assert_called_once()


def test_search_routes_default_num_itineraries(db: Session, client: TestClient, sample_itineraries):
    """Test that num_itineraries defaults to 3."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": {"latitude": 60.1699, "longitude": 24.9384},
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
            },
            headers=headers,
        )

        assert response.status_code == 200
        # Verify service was called with default value
        call_args = mock_service.get_itinaries.call_args
        assert call_args.kwargs["first"] == 3


def test_search_routes_invalid_coordinates(db: Session, client: TestClient):
    """Test route search with invalid coordinates."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    response = client.post(
        "/api/v1/routes/search",
        json={
            "origin": {"latitude": 91.0, "longitude": 24.9384},  # Invalid latitude
            "destination": {"latitude": 60.2055, "longitude": 24.6559},
        },
        headers=headers,
    )

    assert response.status_code == 422  # Validation error


def test_search_routes_missing_origin(db: Session, client: TestClient):
    """Test route search with missing origin."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    response = client.post(
        "/api/v1/routes/search",
        json={
            "destination": {"latitude": 60.2055, "longitude": 24.6559},
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_search_routes_missing_destination(db: Session, client: TestClient):
    """Test route search with missing destination."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    response = client.post(
        "/api/v1/routes/search",
        json={
            "origin": {"latitude": 60.1699, "longitude": 24.9384},
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_search_routes_invalid_num_itineraries_too_low(db: Session, client: TestClient):
    """Test route search with num_itineraries below minimum."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    response = client.post(
        "/api/v1/routes/search",
        json={
            "origin": {"latitude": 60.1699, "longitude": 24.9384},
            "destination": {"latitude": 60.2055, "longitude": 24.6559},
            "num_itineraries": 0,  # Below minimum of 1
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_search_routes_invalid_num_itineraries_too_high(db: Session, client: TestClient):
    """Test route search with num_itineraries above maximum."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    response = client.post(
        "/api/v1/routes/search",
        json={
            "origin": {"latitude": 60.1699, "longitude": 24.9384},
            "destination": {"latitude": 60.2055, "longitude": 24.6559},
            "num_itineraries": 11,  # Above maximum of 10
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_search_routes_hsl_api_error(db: Session, client: TestClient):
    """Test handling of HSL API errors."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(side_effect=RoutingAPIError("API error"))

        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": {"latitude": 60.1699, "longitude": 24.9384},
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
            },
            headers=headers,
        )

        assert response.status_code == 502
        assert "HSL API error" in response.json()["detail"]


def test_search_routes_network_error(db: Session, client: TestClient):
    """Test handling of network errors."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(side_effect=RoutingNetworkError("Network error"))

        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": {"latitude": 60.1699, "longitude": 24.9384},
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
            },
            headers=headers,
        )

        assert response.status_code == 503
        assert "Network error" in response.json()["detail"]


def test_search_routes_data_error(db: Session, client: TestClient):
    """Test handling of data parsing errors."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(side_effect=RoutingDataError("Parse error"))

        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": {"latitude": 60.1699, "longitude": 24.9384},
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
            },
            headers=headers,
        )

        assert response.status_code == 502
        assert "Failed to parse" in response.json()["detail"]


def test_search_routes_empty_result(db: Session, client: TestClient):
    """Test route search with no results."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(return_value=[])

        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": {"latitude": 60.1699, "longitude": 24.9384},
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["itineraries"]) == 0


def test_search_routes_coordinates_validation(db: Session, client: TestClient):
    """Test coordinate validation with various invalid values."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

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
            headers=headers,
        )
        assert response.status_code == 422


def test_search_routes_valid_edge_coordinates(db: Session, client: TestClient, sample_itineraries):
    """Test route search with edge case valid coordinates."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

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
                headers=headers,
            )
            assert response.status_code == 200


def test_search_routes_without_ai_insight(db: Session, client: TestClient, sample_itineraries):
    """Test that route response works without ai_insight in itinerary (graceful degradation)."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch("app.api.v1.endpoints.routes.routing_service") as mock_service:
        mock_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

        response = client.post(
            "/api/v1/routes/search",
            json={
                "origin": {"latitude": 60.1699, "longitude": 24.9384},
                "destination": {"latitude": 60.2055, "longitude": 24.6559},
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify ai_insight is not in the response (removed from RouteSearchResponse)
        assert "ai_insight" not in data
        # When AI service is not available, itineraries should not have ai_insight
        assert "ai_insight" not in data["itineraries"][0]


def test_search_routes_with_ai_insight(db: Session, client: TestClient, sample_itineraries):
    """Test that itinerary schema validates correctly when ai_insight is provided."""
    # Test the schema validation directly
    from app.schemas.geo import Coordinates
    from app.schemas.insight import ItineraryWithInsight, LegWithInsight
    from app.schemas.routes import RouteSearchResponse

    # Create ItineraryWithInsight objects
    itinerary = sample_itineraries[0]
    legs_with_insights = []
    for leg in itinerary.legs:
        leg_with_insight = LegWithInsight(**leg.model_dump(), ai_insight="Leg insight")
        legs_with_insights.append(leg_with_insight)

    itinerary_data = itinerary.model_dump()
    itinerary_data.pop("legs")
    itinerary_with_description = ItineraryWithInsight(
        **itinerary_data,
        ai_insight="This is a fast route with minimal walking.",
        legs=legs_with_insights,
    )

    response_data = RouteSearchResponse(
        origin=Coordinates(latitude=60.1699, longitude=24.9384),
        destination=Coordinates(latitude=60.2055, longitude=24.6559),
        itineraries=[itinerary_with_description],
        search_time=datetime.now(timezone.utc),
    )
    assert response_data.itineraries[0].ai_insight == "This is a fast route with minimal walking."

    # Schema should validate without ai_insight
    response_data_no_ai = RouteSearchResponse(
        origin=Coordinates(latitude=60.1699, longitude=24.9384),
        destination=Coordinates(latitude=60.2055, longitude=24.6559),
        itineraries=sample_itineraries,
        search_time=datetime.now(timezone.utc),
    )
    # ai_insight field removed from RouteSearchResponse
    assert not hasattr(response_data_no_ai, "ai_insight") or (
        hasattr(response_data_no_ai, "ai_insight") and response_data_no_ai.ai_insight is None
    )


def test_search_routes_with_ai_insights_success(
    db: Session, client: TestClient, sample_itineraries
):
    """Test successful route search with AI insights for each leg and itinerary."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch("app.api.v1.endpoints.routes.routing_service") as mock_routing_service:
        with patch("app.api.v1.endpoints.routes.ai_agents_service") as mock_ai_service:
            mock_routing_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

            # Create itineraries with insights
            from app.schemas.insight import ItineraryWithInsight, LegWithInsight

            itineraries_with_insights = []
            for itinerary in sample_itineraries:
                legs_with_insights = []
                for i, leg in enumerate(itinerary.legs):
                    leg_with_insight = LegWithInsight(
                        **leg.model_dump(),
                        ai_insight=(
                            "Short walk to the bus stop."
                            if i == 0
                            else "Express bus with comfortable seats."
                        ),
                    )
                    legs_with_insights.append(leg_with_insight)

                itinerary_data = itinerary.model_dump()
                itinerary_data.pop("legs")  # Remove legs from dump since we're providing our own
                itinerary_with_insights = ItineraryWithInsight(
                    **itinerary_data,
                    ai_insight=(
                        "This route offers a good balance of walking and public transport."
                    ),
                    legs=legs_with_insights,
                )
                itineraries_with_insights.append(itinerary_with_insights)

            mock_ai_service.get_itineraries_with_insights = AsyncMock(
                return_value=itineraries_with_insights
            )

            response = client.post(
                "/api/v1/routes/search",
                json={
                    "origin": {"latitude": 60.1699, "longitude": 24.9384},
                    "destination": {"latitude": 60.2055, "longitude": 24.6559},
                },
                headers=headers,
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

            # Verify AI insight for the itinerary
            assert (
                itinerary["ai_insight"]
                == "This route offers a good balance of walking and public transport."
            )
            # Verify AI service was called for itinerary insight
            assert mock_ai_service.get_itineraries_with_insights.call_count == 1


def test_search_routes_with_ai_service_unavailable(
    db: Session, client: TestClient, sample_itineraries
):
    """Test graceful degradation when AI service is unavailable."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch("app.api.v1.endpoints.routes.routing_service") as mock_routing_service:
        with patch("app.api.v1.endpoints.routes.ai_agents_service") as mock_ai_service:
            mock_routing_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

            # Mock AI service to return empty list (service unavailable)
            mock_ai_service.get_itineraries_with_insights = AsyncMock(return_value=[])

            response = client.post(
                "/api/v1/routes/search",
                json={
                    "origin": {"latitude": 60.1699, "longitude": 24.9384},
                    "destination": {"latitude": 60.2055, "longitude": 24.6559},
                },
                headers=headers,
            )

            # Should still succeed with 200, but without AI insights
            assert response.status_code == 200
            data = response.json()

            # Verify response structure is intact
            assert len(data["itineraries"]) == 1
            itinerary = data["itineraries"][0]
            assert len(itinerary["legs"]) == 2

            # AI insights should not be present when service is unavailable
            assert "ai_insight" not in itinerary["legs"][0]
            assert "ai_insight" not in itinerary["legs"][1]
            # AI insight should not be present when service is unavailable
            assert "ai_insight" not in itinerary


def test_search_routes_with_ai_service_partial_failure(
    db: Session, client: TestClient, sample_itineraries
):
    """Test graceful degradation when AI service provides partial data."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch("app.api.v1.endpoints.routes.routing_service") as mock_routing_service:
        with patch("app.api.v1.endpoints.routes.ai_agents_service") as mock_ai_service:
            mock_routing_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

            # Create itineraries with partial insights (only description, no leg insights)
            from app.schemas.insight import ItineraryWithInsight, LegWithInsight

            itineraries_with_insights = []
            for itinerary in sample_itineraries:
                # Create legs without insights (empty strings)
                legs_with_insights = []
                for leg in itinerary.legs:
                    leg_with_insight = LegWithInsight(
                        **leg.model_dump(), ai_insight=""  # Partial failure - no leg insights
                    )
                    legs_with_insights.append(leg_with_insight)

                itinerary_data = itinerary.model_dump()
                itinerary_data.pop("legs")  # Remove legs from dump since we're providing our own
                itinerary_with_insights = ItineraryWithInsight(
                    **itinerary_data,
                    ai_insight="This is a good route.",
                    legs=legs_with_insights,
                )
                itineraries_with_insights.append(itinerary_with_insights)

            mock_ai_service.get_itineraries_with_insights = AsyncMock(
                return_value=itineraries_with_insights
            )

            response = client.post(
                "/api/v1/routes/search",
                json={
                    "origin": {"latitude": 60.1699, "longitude": 24.9384},
                    "destination": {"latitude": 60.2055, "longitude": 24.6559},
                },
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()

            # Verify itinerary has insight but legs have empty insights (partial failure)
            assert data["itineraries"][0]["ai_insight"] == "This is a good route."
            assert data["itineraries"][0]["legs"][0]["ai_insight"] == ""
            assert data["itineraries"][0]["legs"][1]["ai_insight"] == ""


def test_search_routes_with_ai_service_exception(
    db: Session, client: TestClient, sample_itineraries
):
    """Test graceful degradation when AI service raises an exception."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch("app.api.v1.endpoints.routes.routing_service") as mock_routing_service:
        with patch("app.api.v1.endpoints.routes.ai_agents_service") as mock_ai_service:
            mock_routing_service.get_itinaries = AsyncMock(return_value=sample_itineraries)

            # Mock AI service to raise an exception
            mock_ai_service.get_itineraries_with_insights = AsyncMock(
                side_effect=Exception("AI service error")
            )

            response = client.post(
                "/api/v1/routes/search",
                json={
                    "origin": {"latitude": 60.1699, "longitude": 24.9384},
                    "destination": {"latitude": 60.2055, "longitude": 24.6559},
                },
                headers=headers,
            )

            # Should still succeed with 200, gracefully degrading
            assert response.status_code == 200
            data = response.json()

            # Verify response structure is intact
            assert len(data["itineraries"]) == 1
            itinerary = data["itineraries"][0]
            assert len(itinerary["legs"]) == 2

            # AI insights should not be present due to graceful degradation
            assert "ai_insight" not in itinerary["legs"][0]
            assert "ai_insight" not in itinerary["legs"][1]
            # AI insight should not be present due to graceful degradation
            assert "ai_insight" not in itinerary


def test_leg_schema_with_ai_insight():
    """Test that LegWithInsight schema correctly handles ai_insight field."""
    from app.schemas.insight import LegWithInsight

    # Test leg with ai_insight
    leg_with_insight = LegWithInsight(
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

    # Test leg without ai_insight (regular Leg object)
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
    # Regular Leg objects don't have ai_insight attribute
    assert not hasattr(leg_without_insight, "ai_insight")
