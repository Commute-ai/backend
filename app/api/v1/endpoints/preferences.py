from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.preference import PreferenceCreate, PreferenceResponse
from app.services.auth_service import auth_service
from app.services.preference_service import preference_service

router = APIRouter()


@router.get("", response_model=List[PreferenceResponse])
async def get_user_preferences(
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all preferences for the authenticated user.
    """
    preferences = preference_service.get_user_preferences(
        db, int(current_user.id)
    )
    return preferences


@router.post("", response_model=PreferenceResponse, status_code=201)
async def create_preference(
    preference_in: PreferenceCreate,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Create a new preference for the authenticated user.
    """
    preference = preference_service.create_preference(
        db, int(current_user.id), preference_in
    )
    return preference


@router.delete("/{preference_id}", status_code=204)
async def delete_preference(
    preference_id: int,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a preference for the authenticated user.
    """
    preference_service.delete_preference(
        db, int(current_user.id), preference_id
    )
