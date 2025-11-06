from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.auth_service import auth_service


def test_create_user_table(db: Session):
    """
    Test that we can create a table in the database
    """
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()

    assert "users" in tables


def test_register_user(db: Session, client: TestClient):
    """Test user registration endpoint"""
    user_data = {
        "username": "testuser",
        "password": "testpassword123",
    }

    response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    db_user = (
        db.query(User).filter(User.username == user_data["username"]).first()
    )
    assert db_user is not None
    assert db_user.username == user_data["username"]


def test_register_existing_user(db: Session, client: TestClient):
    """Test registering a user that already exists"""
    username = "testexisting"
    db_user = User(
        username=username,
        hashed_password=auth_service.get_password_hash("testpassword123"),
    )
    db.add(db_user)
    db.commit()

    user_data = {
        "username": username,
        "password": "anotherpassword",
    }

    response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_login_success(db: Session, client: TestClient):
    """Test successful login and token retrieval"""
    username = "testlogin"
    password = "correctpassword"
    db_user = User(
        username=username,
        hashed_password=auth_service.get_password_hash(password),
    )
    db.add(db_user)
    db.commit()

    response = client.post(
        "/api/v1/auth/login", data={"username": username, "password": password}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_incorrect_password(db: Session, client: TestClient):
    """Test login with incorrect password"""
    username = "testuser"
    db_user = User(
        username=username,
        hashed_password=auth_service.get_password_hash("correctpassword"),
    )
    db.add(db_user)
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": "wrongpassword"},
    )

    assert response.status_code == 401
    assert "incorrect username or password" in response.json()["detail"].lower()
