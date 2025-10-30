"""
Authentication service for handling password hashing, verification, and token generation.
"""

from datetime import timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, oauth2_scheme
from app.db.database import get_db
from app.models.user import User
from app.schemas.token import TokenPayload
from app.services.user_service import user_service

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for handling authentication operations."""

    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password to hash

        Returns:
            Hashed password string
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Previously hashed password to check against

        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def generate_access_token(user_id: int) -> str:
        """
        Generate an access token for a user.

        Args:
            user_id: The ID of the user to generate token for

        Returns:
            JWT access token string
        """
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(subject=user_id, expires_delta=access_token_expires)

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user by username and password.

        Args:
            db: Database session
            username: Username to authenticate
            password: Plain text password to verify

        Returns:
            User object if authentication successful, None otherwise
        """
        user = user_service.get_user_by_username(db, username)
        if not user:
            return None
        if not AuthService.verify_password(password, str(user.hashed_password)):
            return None
        return user

    @staticmethod
    def get_current_user(
        db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
    ) -> User:
        """
        Decode JWT token and return the current user.

        Args:
            db: Database session
            token: JWT token from request

        Returns:
            User object for the authenticated user

        Raises:
            HTTPException: If token is invalid or user not found
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            token_data = TokenPayload(**payload)
        except (jwt.JWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )

        user = db.query(User).filter(User.id == int(token_data.sub)).first()  # type: ignore
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    @staticmethod
    def get_current_user_optional(
        db: Session = Depends(get_db),
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    ) -> Optional[User]:
        """
        Decode JWT token and return the current user if authenticated.
        Returns None if no token is provided (allowing anonymous access).

        Args:
            db: Database session
            credentials: Optional HTTP Bearer credentials from request

        Returns:
            User object for the authenticated user, or None if not authenticated

        Raises:
            HTTPException: If token is provided but invalid
        """
        if credentials is None:
            return None

        token = credentials.credentials
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            token_data = TokenPayload(**payload)
        except (jwt.JWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )

        user = db.query(User).filter(User.id == int(token_data.sub)).first()  # type: ignore
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user


# Create a singleton instance
auth_service = AuthService()
