from pydantic import BaseModel


class ServiceHealth(BaseModel):
    healthy: bool
    message: str


class HealthCheckResponse(BaseModel):
    service: str
    version: str
    timestamp: str
    healthy: bool
    database: ServiceHealth
    routing_service: ServiceHealth
    ai_agents_service: ServiceHealth
