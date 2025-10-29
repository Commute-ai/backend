"""
Preference service for handling preference-related business logic.
"""

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.preference import Preference
from app.schemas.preference import PreferenceCreate


class PreferenceService:
    """Service for handling preference operations."""

    @staticmethod
    def get_user_preferences(db: Session, user_id: int) -> List[Preference]:
        """
        Get all preferences for a user.

        Args:
            db: Database session
            user_id: User ID to get preferences for

        Returns:
            List of Preference objects
        """
        return db.query(Preference).filter(Preference.user_id == user_id).all()

    @staticmethod
    def get_preference_by_id(db: Session, preference_id: int) -> Optional[Preference]:
        """
        Get a preference by ID.

        Args:
            db: Database session
            preference_id: Preference ID to search for

        Returns:
            Preference object if found, None otherwise
        """
        return db.query(Preference).filter(Preference.id == preference_id).first()

    @staticmethod
    def create_preference(db: Session, user_id: int, preference_in: PreferenceCreate) -> Preference:
        """
        Create a new preference for a user.

        Args:
            db: Database session
            user_id: User ID to create preference for
            preference_in: Preference creation data

        Returns:
            Created Preference object

        Raises:
            HTTPException: If validation fails
        """
        # Validate prompt is not empty
        if not preference_in.prompt or not preference_in.prompt.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Preference prompt cannot be empty",
            )

        # Create preference
        preference = Preference(
            user_id=user_id,
            prompt=preference_in.prompt.strip(),
        )
        db.add(preference)
        db.commit()
        db.refresh(preference)

        return preference

    @staticmethod
    def delete_preference(db: Session, user_id: int, preference_id: int) -> bool:
        """
        Delete a preference for a user.

        Args:
            db: Database session
            user_id: User ID who owns the preference
            preference_id: Preference ID to delete

        Returns:
            True if deleted successfully

        Raises:
            HTTPException: If preference not found or doesn't belong to user
        """
        preference = db.query(Preference).filter(Preference.id == preference_id).first()

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
preference_service = PreferenceService()
