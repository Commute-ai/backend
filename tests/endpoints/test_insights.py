"""
Unit tests for insights endpoint.
"""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.ai_agents import ItineraryInsight, ItineraryInsightsResponse, LegInsight
from app.schemas.geo import Coordinates
from app.schemas.itinary import Itinerary, Leg, Route, TransportMode
from app.schemas.location import Place
from app.schemas.preference import PreferenceBase
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
def sample_preferences():
    """Create sample user preferences for testing."""
    return [
        PreferenceBase(prompt="I prefer minimal walking"),
        PreferenceBase(prompt="I like direct routes"),
    ]


def test_get_itineraries_insights_success(
    client: TestClient, db: Session, sample_itineraries, sample_preferences
):
    """Test successful itineraries insights retrieval."""
    # Create test user
    user = create_test_user(db)
    auth_header = get_auth_header(user.id)

    # Mock AI agents service response
    mock_response = ItineraryInsightsResponse(
        itenerary_insights=[
            ItineraryInsight(
                ai_insight="This is a convenient route with minimal walking",
                leg_insights=[
                    LegInsight(ai_insight="Short walk to the bus stop"),
                    LegInsight(ai_insight="Express bus with comfortable seats"),
                ],
            )
        ]
    )

    with patch(
        "app.services.ai_agents_service.ai_agents_service.get_itineraries_insights"
    ) as mock_get_insights:
        mock_get_insights.return_value = mock_response

        response = client.post(
            "/api/v1/insight/iteneraries",
            json={
                "itineraries": [
                    itinerary.model_dump(mode="json") for itinerary in sample_itineraries
                ],
                "user_preferences": [pref.model_dump() for pref in sample_preferences],
            },
            headers=auth_header,
        )

        assert response.status_code == 200
        data = response.json()
        assert "itenerary_insights" in data
        assert len(data["itenerary_insights"]) == 1
        assert (
            data["itenerary_insights"][0]["ai_insight"]
            == "This is a convenient route with minimal walking"
        )
        assert len(data["itenerary_insights"][0]["leg_insights"]) == 2
        assert (
            data["itenerary_insights"][0]["leg_insights"][0]["ai_insight"]
            == "Short walk to the bus stop"
        )


def test_get_itineraries_insights_unauthorized(
    client: TestClient, sample_itineraries, sample_preferences
):
    """Test itineraries insights request without authentication."""
    response = client.post(
        "/api/v1/insight/iteneraries",
        json={
            "itineraries": [itinerary.model_dump(mode="json") for itinerary in sample_itineraries],
            "user_preferences": [pref.model_dump() for pref in sample_preferences],
        },
    )

    assert response.status_code == 401


def test_get_itineraries_insights_service_error(
    client: TestClient, db: Session, sample_itineraries, sample_preferences
):
    """Test itineraries insights when service fails."""
    # Create test user
    user = create_test_user(db)
    auth_header = get_auth_header(user.id)

    with patch(
        "app.services.ai_agents_service.ai_agents_service.get_itineraries_insights"
    ) as mock_get_insights:
        mock_get_insights.side_effect = Exception("AI service error")

        response = client.post(
            "/api/v1/insight/iteneraries",
            json={
                "itineraries": [
                    itinerary.model_dump(mode="json") for itinerary in sample_itineraries
                ],
                "user_preferences": [pref.model_dump() for pref in sample_preferences],
            },
            headers=auth_header,
        )

        assert response.status_code == 500
        assert "unexpected error" in response.json()["detail"].lower()


def test_get_itineraries_insights_empty_itineraries(
    client: TestClient, db: Session, sample_preferences
):
    """Test itineraries insights with empty itineraries list."""
    # Create test user
    user = create_test_user(db)
    auth_header = get_auth_header(user.id)

    # Mock AI agents service response for empty list
    mock_response = ItineraryInsightsResponse(itenerary_insights=[])

    with patch(
        "app.services.ai_agents_service.ai_agents_service.get_itineraries_insights"
    ) as mock_get_insights:
        mock_get_insights.return_value = mock_response

        response = client.post(
            "/api/v1/insight/iteneraries",
            json={
                "itineraries": [],
                "user_preferences": [pref.model_dump() for pref in sample_preferences],
            },
            headers=auth_header,
        )

        assert response.status_code == 200
        data = response.json()
        assert "itenerary_insights" in data
        assert len(data["itenerary_insights"]) == 0


def test_get_itineraries_insights_empty_preferences(
    client: TestClient, db: Session, sample_itineraries
):
    """Test itineraries insights with empty preferences list."""
    # Create test user
    user = create_test_user(db)
    auth_header = get_auth_header(user.id)

    # Mock AI agents service response
    mock_response = ItineraryInsightsResponse(
        itenerary_insights=[
            ItineraryInsight(
                ai_insight="Standard route analysis",
                leg_insights=[
                    LegInsight(ai_insight="Walking segment"),
                    LegInsight(ai_insight="Bus segment"),
                ],
            )
        ]
    )

    with patch(
        "app.services.ai_agents_service.ai_agents_service.get_itineraries_insights"
    ) as mock_get_insights:
        mock_get_insights.return_value = mock_response

        response = client.post(
            "/api/v1/insight/iteneraries",
            json={
                "itineraries": [
                    itinerary.model_dump(mode="json") for itinerary in sample_itineraries
                ],
                "user_preferences": [],
            },
            headers=auth_header,
        )

        assert response.status_code == 200
        data = response.json()
        assert "itenerary_insights" in data
        assert len(data["itenerary_insights"]) == 1
