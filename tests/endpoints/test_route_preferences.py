from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.route_preference import RoutePreference
from app.models.user import User
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


def create_test_route_preference(
    db: Session,
    user_id: int,
    prompt: str,
    from_lat: float = 60.1699,
    from_lon: float = 24.9384,
    to_lat: float = 60.2055,
    to_lon: float = 24.6559,
) -> RoutePreference:
    """Helper function to create a test route preference"""
    preference = RoutePreference(
        user_id=user_id,
        prompt=prompt,
        from_latitude=from_lat,
        from_longitude=from_lon,
        to_latitude=to_lat,
        to_longitude=to_lon,
    )
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference


def test_get_route_preferences_empty(db: Session, client: TestClient):
    """Test getting route preferences when user has none"""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    response = client.get("/api/v1/users/route-preferences", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_get_route_preferences(db: Session, client: TestClient):
    """Test getting all route preferences for a user"""
    user = create_test_user(db)
    pref1 = create_test_route_preference(
        db, user.id, "Prefer direct routes", 60.1699, 24.9384, 60.2055, 24.6559
    )
    pref2 = create_test_route_preference(
        db, user.id, "Avoid buses", 60.1699, 24.9384, 60.1951, 24.9402
    )
    headers = get_auth_header(user.id)

    response = client.get("/api/v1/users/route-preferences", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == pref1.id
    assert data[0]["prompt"] == "Prefer direct routes"
    assert data[0]["from_latitude"] == 60.1699
    assert data[0]["from_longitude"] == 24.9384
    assert data[0]["to_latitude"] == 60.2055
    assert data[0]["to_longitude"] == 24.6559
    assert data[1]["id"] == pref2.id
    assert data[1]["prompt"] == "Avoid buses"
    assert "created_at" in data[0]


def test_get_route_preferences_unauthorized(client: TestClient):
    """Test accessing route preferences without authentication"""
    response = client.get("/api/v1/users/route-preferences")

    assert response.status_code == 401


def test_get_route_preferences_invalid_token(client: TestClient):
    """Test accessing route preferences with invalid token"""
    headers = {"Authorization": "Bearer invalidtoken123"}

    response = client.get("/api/v1/users/route-preferences", headers=headers)

    assert response.status_code == 403


def test_create_route_preference(db: Session, client: TestClient):
    """Test creating a new route preference"""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    preference_data = {
        "prompt": "Prefer trains over buses",
        "from_latitude": 60.1699,
        "from_longitude": 24.9384,
        "to_latitude": 60.2055,
        "to_longitude": 24.6559,
    }

    response = client.post(
        "/api/v1/users/route-preferences",
        json=preference_data,
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["prompt"] == "Prefer trains over buses"
    assert data["from_latitude"] == 60.1699
    assert data["from_longitude"] == 24.9384
    assert data["to_latitude"] == 60.2055
    assert data["to_longitude"] == 24.6559
    assert "id" in data
    assert "created_at" in data


def test_create_route_preference_empty_prompt(db: Session, client: TestClient):
    """Test creating a route preference with empty prompt"""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    preference_data = {
        "prompt": "",
        "from_latitude": 60.1699,
        "from_longitude": 24.9384,
        "to_latitude": 60.2055,
        "to_longitude": 24.6559,
    }

    response = client.post(
        "/api/v1/users/route-preferences",
        json=preference_data,
        headers=headers,
    )

    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


def test_create_route_preference_whitespace_only(
    db: Session, client: TestClient
):
    """Test creating a route preference with whitespace-only prompt"""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    preference_data = {
        "prompt": "   ",
        "from_latitude": 60.1699,
        "from_longitude": 24.9384,
        "to_latitude": 60.2055,
        "to_longitude": 24.6559,
    }

    response = client.post(
        "/api/v1/users/route-preferences",
        json=preference_data,
        headers=headers,
    )

    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


def test_create_route_preference_invalid_latitude(
    db: Session, client: TestClient
):
    """Test creating a route preference with invalid latitude"""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    preference_data = {
        "prompt": "Test preference",
        "from_latitude": 91.0,  # Invalid: > 90
        "from_longitude": 24.9384,
        "to_latitude": 60.2055,
        "to_longitude": 24.6559,
    }

    response = client.post(
        "/api/v1/users/route-preferences",
        json=preference_data,
        headers=headers,
    )

    assert response.status_code == 422


def test_create_route_preference_invalid_longitude(
    db: Session, client: TestClient
):
    """Test creating a route preference with invalid longitude"""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    preference_data = {
        "prompt": "Test preference",
        "from_latitude": 60.1699,
        "from_longitude": 181.0,  # Invalid: > 180
        "to_latitude": 60.2055,
        "to_longitude": 24.6559,
    }

    response = client.post(
        "/api/v1/users/route-preferences",
        json=preference_data,
        headers=headers,
    )

    assert response.status_code == 422


def test_create_route_preference_unauthorized(client: TestClient):
    """Test creating a route preference without authentication"""
    preference_data = {
        "prompt": "Test preference",
        "from_latitude": 60.1699,
        "from_longitude": 24.9384,
        "to_latitude": 60.2055,
        "to_longitude": 24.6559,
    }

    response = client.post(
        "/api/v1/users/route-preferences", json=preference_data
    )

    assert response.status_code == 401


def test_create_route_preference_strips_whitespace(
    db: Session, client: TestClient
):
    """Test that creating a route preference strips leading/trailing whitespace"""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    preference_data = {
        "prompt": "  Avoid crowded routes  ",
        "from_latitude": 60.1699,
        "from_longitude": 24.9384,
        "to_latitude": 60.2055,
        "to_longitude": 24.6559,
    }

    response = client.post(
        "/api/v1/users/route-preferences",
        json=preference_data,
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["prompt"] == "Avoid crowded routes"


def test_delete_route_preference(db: Session, client: TestClient):
    """Test deleting a route preference"""
    user = create_test_user(db)
    pref = create_test_route_preference(db, user.id, "Test preference")
    headers = get_auth_header(user.id)

    response = client.delete(
        f"/api/v1/users/route-preferences/{pref.id}",
        headers=headers,
    )

    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(
        "/api/v1/users/route-preferences", headers=headers
    )
    assert len(get_response.json()) == 0


def test_delete_route_preference_not_found(db: Session, client: TestClient):
    """Test deleting a non-existent route preference"""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    response = client.delete(
        "/api/v1/users/route-preferences/99999",
        headers=headers,
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_delete_route_preference_wrong_user(db: Session, client: TestClient):
    """Test deleting another user's route preference"""
    user1 = create_test_user(db, "user1")
    user2 = create_test_user(db, "user2")
    pref = create_test_route_preference(db, user1.id, "User1's preference")

    headers = get_auth_header(user2.id)

    response = client.delete(
        f"/api/v1/users/route-preferences/{pref.id}",
        headers=headers,
    )

    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]


def test_delete_route_preference_unauthorized(client: TestClient):
    """Test deleting a route preference without authentication"""
    response = client.delete("/api/v1/users/route-preferences/1")

    assert response.status_code == 401


def test_multiple_users_route_preferences_isolated(
    db: Session, client: TestClient
):
    """Test that users can only see their own route preferences"""
    user1 = create_test_user(db, "user1")
    user2 = create_test_user(db, "user2")

    create_test_route_preference(db, user1.id, "User1 preference 1")
    create_test_route_preference(db, user1.id, "User1 preference 2")
    create_test_route_preference(db, user2.id, "User2 preference 1")

    # User1 should only see their preferences
    headers1 = get_auth_header(user1.id)
    response1 = client.get("/api/v1/users/route-preferences", headers=headers1)
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1) == 2
    assert all(pref["prompt"].startswith("User1") for pref in data1)

    # User2 should only see their preferences
    headers2 = get_auth_header(user2.id)
    response2 = client.get("/api/v1/users/route-preferences", headers=headers2)
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2) == 1
    assert data2[0]["prompt"] == "User2 preference 1"


def test_create_route_preference_valid_edge_coordinates(
    db: Session, client: TestClient
):
    """Test creating a route preference with valid edge case coordinates"""
    user = create_test_user(db)
    headers = get_auth_header(user.id)

    preference_data = {
        "prompt": "Edge case test",
        "from_latitude": -90.0,  # Min valid latitude
        "from_longitude": -180.0,  # Min valid longitude
        "to_latitude": 90.0,  # Max valid latitude
        "to_longitude": 180.0,  # Max valid longitude
    }

    response = client.post(
        "/api/v1/users/route-preferences",
        json=preference_data,
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["from_latitude"] == -90.0
    assert data["from_longitude"] == -180.0
    assert data["to_latitude"] == 90.0
    assert data["to_longitude"] == 180.0
