from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.route_preference import (
    RoutePreferenceCreate,
    RoutePreferenceResponse,
)
from app.services.auth_service import auth_service
from app.services.route_preference_service import route_preference_service

router = APIRouter()


@router.get("", response_model=List[RoutePreferenceResponse])
async def get_user_route_preferences(
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get all route preferences for the authenticated user.
    """
    preferences = route_preference_service.get_user_preferences(
        db, int(current_user.id)
    )
    return preferences


@router.post("", response_model=RoutePreferenceResponse, status_code=201)
async def create_route_preference(
    preference_in: RoutePreferenceCreate,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Create a new route preference for the authenticated user.
    """
    preference = route_preference_service.create_preference(
        db, int(current_user.id), preference_in
    )
    return preference


@router.delete("/{preference_id}", status_code=204)
async def delete_route_preference(
    preference_id: int,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a route preference for the authenticated user.
    """
    route_preference_service.delete_preference(
        db, int(current_user.id), preference_id
    )
