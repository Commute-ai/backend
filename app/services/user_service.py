"""
User service for handling user-related business logic.
"""
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


class UserService:
    """Service for handling user operations."""

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """
        Get a user by username.

        Args:
            db: Database session
            username: Username to search for

        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            db: Database session
            user_id: User ID to search for

        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.id == user_id).first()

    @classmethod
    def create_user(cls, db: Session, user_in: UserCreate, hashed_password: str) -> User:
        """
        Create a new user in the database.

        Args:
            db: Database session
            user_in: User creation data
            hashed_password: Pre-hashed password for the user

        Returns:
            Created User object

        Raises:
            HTTPException: If user already exists or validation fails
        """
        # Check if user already exists
        existing_user = cls.get_user_by_username(db, user_in.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this username already exists",
            )

        # Validate username length
        if len(user_in.username) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username must be at least 3 characters",
            )

        # Validate password length
        if len(user_in.password) < 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 4 characters",
            )

        # Create user
        user = User(
            username=user_in.username,
            hashed_password=hashed_password,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return user


# Create a singleton instance
user_service = UserService()
