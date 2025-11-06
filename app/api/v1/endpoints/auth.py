from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.token import Token
from app.schemas.user import UserCreate
from app.services.auth_service import auth_service
from app.services.user_service import user_service

router = APIRouter()


@router.post("/register", response_model=Token)
async def register_user(
    user_in: UserCreate, db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user.
    """
    # Hash the password
    hashed_password = auth_service.get_password_hash(user_in.password)

    # Create the user (this includes validation)
    user = user_service.create_user(db, user_in, hashed_password)

    # Generate access token
    access_token = auth_service.generate_access_token(int(user.id))

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # Authenticate user
    user = auth_service.authenticate_user(
        db, form_data.username, form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate access token
    access_token = auth_service.generate_access_token(int(user.id))

    return {"access_token": access_token, "token_type": "bearer"}
