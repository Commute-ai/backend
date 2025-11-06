from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, preferences, routes, users

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    preferences.router, prefix="/users/preferences", tags=["preferences"]
)
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
