import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.preference import Preference
from app.models.user import User
from app.schemas.preference import PreferenceCreate
from app.services.auth_service import auth_service
from app.services.preference_service import preference_service


def create_test_user(db: Session) -> User:
    """Helper function to create a test user"""
    user = User(
        username="testuser",
        hashed_password=auth_service.get_password_hash("testpassword"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_test_preference(db: Session, user_id: int, prompt: str) -> Preference:
    """Helper function to create a test preference"""
    preference = Preference(user_id=user_id, prompt=prompt)
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference


def test_get_user_preferences_empty(db: Session):
    """Test getting preferences when user has none"""
    user = create_test_user(db)

    preferences = preference_service.get_user_preferences(db, user.id)

    assert preferences == []


def test_get_user_preferences(db: Session):
    """Test getting preferences for a user"""
    user = create_test_user(db)
    pref1 = create_test_preference(db, user.id, "Prefer direct routes")
    pref2 = create_test_preference(db, user.id, "Avoid buses")

    preferences = preference_service.get_user_preferences(db, user.id)

    assert len(preferences) == 2
    assert preferences[0].id == pref1.id
    assert preferences[0].prompt == "Prefer direct routes"
    assert preferences[1].id == pref2.id
    assert preferences[1].prompt == "Avoid buses"


def test_get_preference_by_id(db: Session):
    """Test getting a preference by ID"""
    user = create_test_user(db)
    pref = create_test_preference(db, user.id, "Test preference")

    result = preference_service.get_preference_by_id(db, pref.id)

    assert result is not None
    assert result.id == pref.id
    assert result.prompt == "Test preference"


def test_get_preference_by_id_not_found(db: Session):
    """Test getting a non-existent preference"""
    result = preference_service.get_preference_by_id(db, 99999)

    assert result is None


def test_create_preference(db: Session):
    """Test creating a new preference"""
    user = create_test_user(db)
    preference_in = PreferenceCreate(prompt="Prefer trains over buses")

    preference = preference_service.create_preference(db, user.id, preference_in)

    assert preference.id is not None
    assert preference.user_id == user.id
    assert preference.prompt == "Prefer trains over buses"
    assert preference.created_at is not None


def test_create_preference_strips_whitespace(db: Session):
    """Test that creating a preference strips leading/trailing whitespace"""
    user = create_test_user(db)
    preference_in = PreferenceCreate(prompt="  Avoid crowded routes  ")

    preference = preference_service.create_preference(db, user.id, preference_in)

    assert preference.prompt == "Avoid crowded routes"


def test_create_preference_empty_prompt(db: Session):
    """Test creating a preference with empty prompt raises error"""
    user = create_test_user(db)
    preference_in = PreferenceCreate(prompt="")

    with pytest.raises(HTTPException) as exc_info:
        preference_service.create_preference(db, user.id, preference_in)

    assert exc_info.value.status_code == 400
    assert "cannot be empty" in exc_info.value.detail


def test_create_preference_whitespace_only_prompt(db: Session):
    """Test creating a preference with whitespace-only prompt raises error"""
    user = create_test_user(db)
    preference_in = PreferenceCreate(prompt="   ")

    with pytest.raises(HTTPException) as exc_info:
        preference_service.create_preference(db, user.id, preference_in)

    assert exc_info.value.status_code == 400
    assert "cannot be empty" in exc_info.value.detail


def test_delete_preference(db: Session):
    """Test deleting a preference"""
    user = create_test_user(db)
    pref = create_test_preference(db, user.id, "Test preference")

    result = preference_service.delete_preference(db, user.id, pref.id)

    assert result is True
    # Verify it's deleted
    deleted_pref = preference_service.get_preference_by_id(db, pref.id)
    assert deleted_pref is None


def test_delete_preference_not_found(db: Session):
    """Test deleting a non-existent preference raises error"""
    user = create_test_user(db)

    with pytest.raises(HTTPException) as exc_info:
        preference_service.delete_preference(db, user.id, 99999)

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail


def test_delete_preference_wrong_user(db: Session):
    """Test deleting another user's preference raises error"""
    user1 = create_test_user(db)
    user2 = User(
        username="otheruser",
        hashed_password=auth_service.get_password_hash("password"),
    )
    db.add(user2)
    db.commit()
    db.refresh(user2)

    pref = create_test_preference(db, user1.id, "User1's preference")

    with pytest.raises(HTTPException) as exc_info:
        preference_service.delete_preference(db, user2.id, pref.id)

    assert exc_info.value.status_code == 403
    assert "Not authorized" in exc_info.value.detail
