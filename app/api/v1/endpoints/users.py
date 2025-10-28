from typing import Any

from fastapi import APIRouter, Depends

from app.models.user import User
from app.schemas.user import UserResponse
from app.services.auth_service import auth_service

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(auth_service.get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user
