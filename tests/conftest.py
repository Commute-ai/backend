import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test database URL - using SQLite for tests is simpler
SQLALCHEMY_DATABASE_TEST_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


@pytest.fixture(scope="function")
def db():
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db):
    """Provides a FastAPI test client with test database."""

    def override_get_db():
        try:
            yield db
        finally:
            pass  # Cleanup handled by db fixture

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    # Clean up overrides after test
    app.dependency_overrides.clear()
