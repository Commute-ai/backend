from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import database
from app.db.database import get_db
from app.schemas.health import HealthCheckResponse
from app.services import ai_agents_service, routing_service

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)) -> HealthCheckResponse:
    """
    Comprehensive health check endpoint that verifies:
    - Database connectivity
    - HSL API availability
    - AI-agents API availability

    Returns 200 if all services are healthy, 503 if any service is down.
    """
    # Ping all services using their own health_check methods
    database_health = database.health_check(db)
    routing_service_health = await routing_service.health_check()
    ai_agents_service_health = await ai_agents_service.health_check()

    # Determine overall health
    overall_healthy = all(
        [database_health.healthy, routing_service_health.healthy, ai_agents_service_health.healthy]
    )

    response = HealthCheckResponse(
        service="commute-ai-backend",
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        healthy=overall_healthy,
        database=database_health,
        routing_service=routing_service_health,
        ai_agents_service=ai_agents_service_health,
    )

    # Return appropriate status code
    if overall_healthy:
        return response
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response.model_dump()
    )
