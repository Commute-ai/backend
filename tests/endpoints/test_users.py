from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


def create_test_user(db: Session):
    """Helper function to create a test user and return its data"""
    username = "testuser"
    user = User(
        username=username,
        hashed_password=get_password_hash("testpassword"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_header(user_id: int):
    """Helper function to generate authorization header with token"""
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}"}


def test_create_user_table(db: Session):
    """
    Test that we can create a table in the database
    """
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()

    assert "users" in tables


def test_read_current_user(db: Session, client: TestClient):
    """Test getting the current user details"""
    user = create_test_user(db)

    headers = get_auth_header(user.id)

    response = client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == user.username
    assert data["id"] == user.id


def test_read_current_user_unauthorized(client: TestClient):
    """Test accessing current user without token"""
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert "not authenticated" in response.json()["detail"].lower()


def test_invalid_token(client: TestClient):
    """Test using an invalid token"""
    headers = {"Authorization": "Bearer invalidtoken123"}

    response = client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 403
    assert "could not validate credentials" in response.json()["detail"].lower()
