"""
Unit tests for routes endpoint with user preferences integration.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.preference import Preference
from app.models.user import User
from app.schemas.geo import Coordinates
from app.schemas.itinary import Itinerary, Leg, Route, TransportMode
from app.schemas.location import Place
from app.services.auth_service import auth_service


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
                        coordinates=Coordinates(
                            latitude=60.1699, longitude=24.9384
                        ),
                        name="Origin",
                    ),
                    to_place=Place(
                        coordinates=Coordinates(
                            latitude=60.1710, longitude=24.9400
                        ),
                        name="Bus Stop",
                    ),
                    route=None,
                ),
                Leg(
                    mode=TransportMode.BUS,
                    start=datetime(
                        2025, 10, 14, 10, 10, 0, tzinfo=timezone.utc
                    ),
                    end=datetime(2025, 10, 14, 10, 45, 0, tzinfo=timezone.utc),
                    duration=2100,
                    distance=15000.0,
                    from_place=Place(
                        coordinates=Coordinates(
                            latitude=60.1710, longitude=24.9400
                        ),
                        name="Bus Stop",
                    ),
                    to_place=Place(
                        coordinates=Coordinates(
                            latitude=60.2055, longitude=24.6559
                        ),
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


def test_search_routes_with_request_preferences(
    db: Session, client: TestClient, sample_itineraries
):
    """Test route search with preferences provided in request."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch(
        "app.api.v1.endpoints.routes.routing_service"
    ) as mock_routing_service:
        with patch(
            "app.api.v1.endpoints.routes.ai_agents_service"
        ) as mock_ai_service:
            mock_routing_service.get_itinaries = AsyncMock(
                return_value=sample_itineraries
            )

            # Create itineraries with insights
            from app.schemas.insight import ItineraryWithInsight, LegWithInsight

            itineraries_with_insights = []
            for itinerary in sample_itineraries:
                legs_with_insights = []
                for leg in itinerary.legs:
                    leg_with_insight = LegWithInsight(
                        **leg.model_dump(), ai_insight="Optimized leg insight"
                    )
                    legs_with_insights.append(leg_with_insight)

                itinerary_data = itinerary.model_dump()
                itinerary_data.pop(
                    "legs"
                )  # Remove legs from dump since we're providing our own
                itinerary_with_insights = ItineraryWithInsight(
                    **itinerary_data,
                    ai_insight="Route optimized based on preferences",
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
                    "preferences": ["prefer walking", "avoid crowded buses"],
                },
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["itineraries"]) == 1

            # Verify AI service was called with preferences
            mock_ai_service.get_itineraries_with_insights.assert_called_once()
            call_args = mock_ai_service.get_itineraries_with_insights.call_args
            assert call_args.args[0] == sample_itineraries
            assert call_args.args[1] == [
                "prefer walking",
                "avoid crowded buses",
            ]


def test_search_routes_with_authenticated_user_preferences(
    db: Session, client: TestClient, sample_itineraries
):
    """Test route search with authenticated user and stored preferences."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch(
        "app.api.v1.endpoints.routes.routing_service"
    ) as mock_routing_service:
        with patch(
            "app.api.v1.endpoints.routes.ai_agents_service"
        ) as mock_ai_service:
            with patch(
                "app.api.v1.endpoints.routes.preference_service"
            ) as mock_pref_service:
                mock_routing_service.get_itinaries = AsyncMock(
                    return_value=sample_itineraries
                )

                # Mock stored preferences for the user
                stored_prefs = [
                    Preference(
                        user_id=1, prompt="I prefer eco-friendly routes"
                    ),
                    Preference(user_id=1, prompt="Avoid long walks"),
                ]
                mock_pref_service.get_user_preferences = MagicMock(
                    return_value=stored_prefs
                )

                # Track the call to verify preferences are passed
                captured_preferences = []

                def mock_get_itineraries_with_insights(
                    itineraries, user_preferences=None
                ):
                    captured_preferences.append(user_preferences)

                mock_ai_service.get_itineraries_with_insights = AsyncMock(
                    side_effect=mock_get_itineraries_with_insights
                )

                response = client.post(
                    "/api/v1/routes/search",
                    json={
                        "origin": {"latitude": 60.1699, "longitude": 24.9384},
                        "destination": {
                            "latitude": 60.2055,
                            "longitude": 24.6559,
                        },
                    },
                    headers=headers,
                )

                assert response.status_code == 200
                data = response.json()
                assert len(data["itineraries"]) == 1

                # Verify AI service was called with stored preferences
                assert len(captured_preferences) == 1
                assert "I prefer eco-friendly routes" in captured_preferences[0]
                assert "Avoid long walks" in captured_preferences[0]


def test_search_routes_with_request_only_preferences(
    db: Session, client: TestClient, sample_itineraries
):
    """Test route search with preferences only from request (no authentication)."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch(
        "app.api.v1.endpoints.routes.routing_service"
    ) as mock_routing_service:
        with patch(
            "app.api.v1.endpoints.routes.ai_agents_service"
        ) as mock_ai_service:
            mock_routing_service.get_itinaries = AsyncMock(
                return_value=sample_itineraries
            )

            # Track the call to verify preferences
            captured_preferences = []

            def mock_get_itineraries_with_insights(
                itineraries, user_preferences=None
            ):
                captured_preferences.append(user_preferences)

            mock_ai_service.get_itineraries_with_insights = AsyncMock(
                side_effect=mock_get_itineraries_with_insights
            )

            response = client.post(
                "/api/v1/routes/search",
                json={
                    "origin": {"latitude": 60.1699, "longitude": 24.9384},
                    "destination": {"latitude": 60.2055, "longitude": 24.6559},
                    "preferences": ["prefer trams", "avoid crowded buses"],
                },
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["itineraries"]) == 1

            # Verify AI service was called with request preferences only
            assert len(captured_preferences) == 1
            assert "prefer trams" in captured_preferences[0]
            assert "avoid crowded buses" in captured_preferences[0]
            assert len(captured_preferences[0]) == 2  # Only request preferences


def test_search_routes_without_preferences(
    db: Session, client: TestClient, sample_itineraries
):
    """Test route search without any preferences (should pass None to AI service)."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch(
        "app.api.v1.endpoints.routes.routing_service"
    ) as mock_routing_service:
        with patch(
            "app.api.v1.endpoints.routes.ai_agents_service"
        ) as mock_ai_service:
            mock_routing_service.get_itinaries = AsyncMock(
                return_value=sample_itineraries
            )

            # Track the call to verify no preferences are passed
            captured_preferences = []

            def mock_get_itineraries_with_insights(
                itineraries, user_preferences=None
            ):
                captured_preferences.append(user_preferences)

            mock_ai_service.get_itineraries_with_insights = AsyncMock(
                side_effect=mock_get_itineraries_with_insights
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
            assert len(data["itineraries"]) == 1

            # Verify AI service was called with None preferences
            assert len(captured_preferences) == 1
            assert captured_preferences[0] is None


def test_search_routes_preference_service_graceful_degradation(
    db: Session, client: TestClient, sample_itineraries
):
    """Test that route search still works when preferences are empty."""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    with patch(
        "app.api.v1.endpoints.routes.routing_service"
    ) as mock_routing_service:
        with patch(
            "app.api.v1.endpoints.routes.ai_agents_service"
        ) as mock_ai_service:
            mock_routing_service.get_itinaries = AsyncMock(
                return_value=sample_itineraries
            )

            # Track the call to verify preferences handling
            captured_preferences = []

            def mock_get_itineraries_with_insights(
                itineraries, user_preferences=None
            ):
                captured_preferences.append(user_preferences)

            mock_ai_service.get_itineraries_with_insights = AsyncMock(
                side_effect=mock_get_itineraries_with_insights
            )

            response = client.post(
                "/api/v1/routes/search",
                json={
                    "origin": {"latitude": 60.1699, "longitude": 24.9384},
                    "destination": {"latitude": 60.2055, "longitude": 24.6559},
                },
                headers=headers,
            )

            # Should succeed without preferences
            assert response.status_code == 200
            data = response.json()
            assert len(data["itineraries"]) == 1

            # Verify AI service was called with None (user has no stored preferences)
            assert len(captured_preferences) == 1
            # User has no preferences, so empty list gets passed as None
            assert (
                captured_preferences[0] is None or captured_preferences[0] == []
            )
