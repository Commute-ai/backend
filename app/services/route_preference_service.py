"""
Route preference service for handling route-specific preference business logic.
"""

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.route_preference import RoutePreference
from app.schemas.route_preference import RoutePreferenceCreate


class RoutePreferenceService:
    """Service for handling route preference operations."""

    @staticmethod
    def get_user_preferences(
        db: Session, user_id: int
    ) -> List[RoutePreference]:
        """
        Get all route preferences for a user.

        Args:
            db: Database session
            user_id: User ID to get preferences for

        Returns:
            List of RoutePreference objects
        """
        return (
            db.query(RoutePreference)
            .filter(RoutePreference.user_id == user_id)
            .all()
        )

    @staticmethod
    def get_preference_by_id(
        db: Session, preference_id: int
    ) -> Optional[RoutePreference]:
        """
        Get a route preference by ID.

        Args:
            db: Database session
            preference_id: Preference ID to search for

        Returns:
            RoutePreference object if found, None otherwise
        """
        return (
            db.query(RoutePreference)
            .filter(RoutePreference.id == preference_id)
            .first()
        )

    @staticmethod
    def create_preference(
        db: Session, user_id: int, preference_in: RoutePreferenceCreate
    ) -> RoutePreference:
        """
        Create a new route preference for a user.

        Args:
            db: Database session
            user_id: User ID to create preference for
            preference_in: Preference creation data

        Returns:
            Created RoutePreference object

        Raises:
            HTTPException: If validation fails
        """
        # Validate prompt is not empty
        if not preference_in.prompt.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Preference prompt cannot be empty",
            )

        # Create preference
        preference = RoutePreference(
            user_id=user_id,
            prompt=preference_in.prompt.strip(),
            from_latitude=preference_in.from_latitude,
            from_longitude=preference_in.from_longitude,
            to_latitude=preference_in.to_latitude,
            to_longitude=preference_in.to_longitude,
        )
        db.add(preference)
        db.commit()
        db.refresh(preference)

        return preference

    @staticmethod
    def delete_preference(
        db: Session, user_id: int, preference_id: int
    ) -> bool:
        """
        Delete a route preference for a user.

        Args:
            db: Database session
            user_id: User ID who owns the preference
            preference_id: Preference ID to delete

        Returns:
            True if deleted successfully

        Raises:
            HTTPException: If preference not found or doesn't belong to user
        """
        preference = (
            db.query(RoutePreference)
            .filter(RoutePreference.id == preference_id)
            .first()
        )

        if not preference:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preference not found",
            )

        # Verify the preference belongs to the user
        if preference.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this preference",
            )

        db.delete(preference)
        db.commit()

        return True


# Create a singleton instance
route_preference_service = RoutePreferenceService()
