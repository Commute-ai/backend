import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.route_preference import RoutePreference
from app.models.user import User
from app.schemas.route_preference import RoutePreferenceCreate
from app.services.auth_service import auth_service
from app.services.route_preference_service import route_preference_service


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


def test_get_user_preferences_empty(db: Session):
    """Test getting preferences when user has none"""
    user = create_test_user(db)

    preferences = route_preference_service.get_user_preferences(db, user.id)

    assert preferences == []


def test_get_user_preferences(db: Session):
    """Test getting preferences for a user"""
    user = create_test_user(db)
    pref1 = create_test_route_preference(
        db, user.id, "Prefer direct routes", 60.1699, 24.9384, 60.2055, 24.6559
    )
    pref2 = create_test_route_preference(
        db, user.id, "Avoid buses", 60.1699, 24.9384, 60.1951, 24.9402
    )

    preferences = route_preference_service.get_user_preferences(db, user.id)

    assert len(preferences) == 2
    assert preferences[0].id == pref1.id
    assert preferences[0].prompt == "Prefer direct routes"
    assert preferences[0].from_latitude == 60.1699
    assert preferences[0].from_longitude == 24.9384
    assert preferences[0].to_latitude == 60.2055
    assert preferences[0].to_longitude == 24.6559
    assert preferences[1].id == pref2.id
    assert preferences[1].prompt == "Avoid buses"


def test_get_preference_by_id(db: Session):
    """Test getting a preference by ID"""
    user = create_test_user(db)
    pref = create_test_route_preference(db, user.id, "Test preference")

    result = route_preference_service.get_preference_by_id(db, pref.id)

    assert result is not None
    assert result.id == pref.id
    assert result.prompt == "Test preference"


def test_get_preference_by_id_not_found(db: Session):
    """Test getting a non-existent preference"""
    result = route_preference_service.get_preference_by_id(db, 99999)

    assert result is None


def test_create_preference(db: Session):
    """Test creating a new preference"""
    user = create_test_user(db)
    preference_in = RoutePreferenceCreate(
        prompt="Prefer trains over buses",
        from_latitude=60.1699,
        from_longitude=24.9384,
        to_latitude=60.2055,
        to_longitude=24.6559,
    )

    preference = route_preference_service.create_preference(
        db, user.id, preference_in
    )

    assert preference.id is not None
    assert preference.user_id == user.id
    assert preference.prompt == "Prefer trains over buses"
    assert preference.from_latitude == 60.1699
    assert preference.from_longitude == 24.9384
    assert preference.to_latitude == 60.2055
    assert preference.to_longitude == 24.6559
    assert preference.created_at is not None


def test_create_preference_strips_whitespace(db: Session):
    """Test that creating a preference strips leading/trailing whitespace"""
    user = create_test_user(db)
    preference_in = RoutePreferenceCreate(
        prompt="  Avoid crowded routes  ",
        from_latitude=60.1699,
        from_longitude=24.9384,
        to_latitude=60.2055,
        to_longitude=24.6559,
    )

    preference = route_preference_service.create_preference(
        db, user.id, preference_in
    )

    assert preference.prompt == "Avoid crowded routes"


def test_create_preference_empty_prompt(db: Session):
    """Test creating a preference with empty prompt raises error"""
    user = create_test_user(db)
    preference_in = RoutePreferenceCreate(
        prompt="",
        from_latitude=60.1699,
        from_longitude=24.9384,
        to_latitude=60.2055,
        to_longitude=24.6559,
    )

    with pytest.raises(HTTPException) as exc_info:
        route_preference_service.create_preference(db, user.id, preference_in)

    assert exc_info.value.status_code == 400
    assert "cannot be empty" in exc_info.value.detail


def test_create_preference_whitespace_only_prompt(db: Session):
    """Test creating a preference with whitespace-only prompt raises error"""
    user = create_test_user(db)
    preference_in = RoutePreferenceCreate(
        prompt="   ",
        from_latitude=60.1699,
        from_longitude=24.9384,
        to_latitude=60.2055,
        to_longitude=24.6559,
    )

    with pytest.raises(HTTPException) as exc_info:
        route_preference_service.create_preference(db, user.id, preference_in)

    assert exc_info.value.status_code == 400
    assert "cannot be empty" in exc_info.value.detail


def test_delete_preference(db: Session):
    """Test deleting a preference"""
    user = create_test_user(db)
    pref = create_test_route_preference(db, user.id, "Test preference")

    result = route_preference_service.delete_preference(db, user.id, pref.id)

    assert result is True
    # Verify it's deleted
    deleted_pref = route_preference_service.get_preference_by_id(db, pref.id)
    assert deleted_pref is None


def test_delete_preference_not_found(db: Session):
    """Test deleting a non-existent preference raises error"""
    user = create_test_user(db)

    with pytest.raises(HTTPException) as exc_info:
        route_preference_service.delete_preference(db, user.id, 99999)

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

    pref = create_test_route_preference(db, user1.id, "User1's preference")

    with pytest.raises(HTTPException) as exc_info:
        route_preference_service.delete_preference(db, user2.id, pref.id)

    assert exc_info.value.status_code == 403
    assert "Not authorized" in exc_info.value.detail


def test_create_preference_with_edge_coordinates(db: Session):
    """Test creating a preference with edge case valid coordinates"""
    user = create_test_user(db)
    preference_in = RoutePreferenceCreate(
        prompt="Edge case test",
        from_latitude=-90.0,
        from_longitude=-180.0,
        to_latitude=90.0,
        to_longitude=180.0,
    )

    preference = route_preference_service.create_preference(
        db, user.id, preference_in
    )

    assert preference.from_latitude == -90.0
    assert preference.from_longitude == -180.0
    assert preference.to_latitude == 90.0
    assert preference.to_longitude == 180.0


def test_multiple_users_preferences_isolated(db: Session):
    """Test that users can only see their own preferences"""
    user1 = create_test_user(db)
    user2 = User(
        username="otheruser",
        hashed_password=auth_service.get_password_hash("password"),
    )
    db.add(user2)
    db.commit()
    db.refresh(user2)

    # Create preferences for both users
    create_test_route_preference(db, user1.id, "User1 preference 1")
    create_test_route_preference(db, user1.id, "User1 preference 2")
    create_test_route_preference(db, user2.id, "User2 preference 1")

    # User1 should only see their preferences
    user1_prefs = route_preference_service.get_user_preferences(db, user1.id)
    assert len(user1_prefs) == 2
    assert all(pref.user_id == user1.id for pref in user1_prefs)

    # User2 should only see their preferences
    user2_prefs = route_preference_service.get_user_preferences(db, user2.id)
    assert len(user2_prefs) == 1
    assert all(pref.user_id == user2.id for pref in user2_prefs)


def test_get_preferences_by_coordinates_matching(db: Session):
    """Test getting preferences by matching coordinates"""
    user = create_test_user(db)

    # Create preferences with different coordinates
    pref1 = create_test_route_preference(
        db, user.id, "Prefer scenic route", 60.1699, 24.9384, 60.2055, 24.6559
    )
    create_test_route_preference(
        db, user.id, "Different route", 60.1700, 24.9400, 60.2060, 24.6600
    )

    # Search for preferences matching specific coordinates
    matching_prefs = route_preference_service.get_preferences_by_coordinates(
        db, user.id, 60.1699, 24.9384, 60.2055, 24.6559
    )

    assert len(matching_prefs) == 1
    assert matching_prefs[0].id == pref1.id
    assert matching_prefs[0].prompt == "Prefer scenic route"


def test_get_preferences_by_coordinates_no_match(db: Session):
    """Test getting preferences when coordinates don't match"""
    user = create_test_user(db)

    # Create preference with specific coordinates
    create_test_route_preference(
        db, user.id, "Prefer scenic route", 60.1699, 24.9384, 60.2055, 24.6559
    )

    # Search with different coordinates
    matching_prefs = route_preference_service.get_preferences_by_coordinates(
        db, user.id, 60.1700, 24.9400, 60.2060, 24.6600
    )

    assert len(matching_prefs) == 0


def test_get_preferences_by_coordinates_multiple_matches(db: Session):
    """Test getting multiple preferences matching the same coordinates"""
    user = create_test_user(db)

    # Create multiple preferences with same coordinates
    pref1 = create_test_route_preference(
        db, user.id, "Prefer scenic route", 60.1699, 24.9384, 60.2055, 24.6559
    )
    pref2 = create_test_route_preference(
        db, user.id, "Avoid construction", 60.1699, 24.9384, 60.2055, 24.6559
    )

    # Search for preferences matching coordinates
    matching_prefs = route_preference_service.get_preferences_by_coordinates(
        db, user.id, 60.1699, 24.9384, 60.2055, 24.6559
    )

    assert len(matching_prefs) == 2
    assert matching_prefs[0].id == pref1.id
    assert matching_prefs[1].id == pref2.id


def test_get_preferences_by_coordinates_user_isolation(db: Session):
    """Test that coordinate search is isolated per user"""
    user1 = create_test_user(db)
    user2 = User(
        username="otheruser",
        hashed_password=auth_service.get_password_hash("password"),
    )
    db.add(user2)
    db.commit()
    db.refresh(user2)

    # Create preferences for both users with same coordinates
    create_test_route_preference(
        db, user1.id, "User1 preference", 60.1699, 24.9384, 60.2055, 24.6559
    )
    create_test_route_preference(
        db, user2.id, "User2 preference", 60.1699, 24.9384, 60.2055, 24.6559
    )

    # User1 should only see their preference
    user1_prefs = route_preference_service.get_preferences_by_coordinates(
        db, user1.id, 60.1699, 24.9384, 60.2055, 24.6559
    )
    assert len(user1_prefs) == 1
    assert user1_prefs[0].prompt == "User1 preference"

    # User2 should only see their preference
    user2_prefs = route_preference_service.get_preferences_by_coordinates(
        db, user2.id, 60.1699, 24.9384, 60.2055, 24.6559
    )
    assert len(user2_prefs) == 1
    assert user2_prefs[0].prompt == "User2 preference"


def test_get_preferences_by_coordinates_partial_match(db: Session):
    """Test that partial coordinate matches don't return results"""
    user = create_test_user(db)

    # Create preference with specific coordinates
    create_test_route_preference(
        db, user.id, "Prefer scenic route", 60.1699, 24.9384, 60.2055, 24.6559
    )

    # Try matching with only origin coordinates correct
    matching_prefs = route_preference_service.get_preferences_by_coordinates(
        db, user.id, 60.1699, 24.9384, 60.9999, 24.9999
    )
    assert len(matching_prefs) == 0

    # Try matching with only destination coordinates correct
    matching_prefs = route_preference_service.get_preferences_by_coordinates(
        db, user.id, 60.9999, 24.9999, 60.2055, 24.6559
    )
    assert len(matching_prefs) == 0
