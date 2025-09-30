from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User


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
        "email": "testregister@example.com",
        "password": "testpassword123",
    }

    response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    db_user = db.query(User).filter(User.email == user_data["email"]).first()
    assert db_user is not None
    assert db_user.email == user_data["email"]


def test_register_existing_user(db: Session, client: TestClient):
    """Test registering a user that already exists"""
    email = "testexisting@example.com"
    db_user = User(
        email=email,
        hashed_password=get_password_hash("testpassword123"),
    )
    db.add(db_user)
    db.commit()

    user_data = {
        "email": email,
        "password": "anotherpassword",
    }

    response = client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_login_success(db: Session, client: TestClient):
    """Test successful login and token retrieval"""
    email = "testlogin@example.com"
    password = "correctpassword"
    db_user = User(
        email=email,
        hashed_password=get_password_hash(password),
    )
    db.add(db_user)
    db.commit()

    response = client.post("/api/v1/auth/login", data={"username": email, "password": password})

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_incorrect_password(db: Session, client: TestClient):
    """Test login with incorrect password"""
    email = "wrongpassword@example.com"
    db_user = User(
        email=email,
        hashed_password=get_password_hash("correctpassword"),
    )
    db.add(db_user)
    db.commit()

    response = client.post(
        "/api/v1/auth/login", data={"username": email, "password": "wrongpassword"}
    )

    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()
