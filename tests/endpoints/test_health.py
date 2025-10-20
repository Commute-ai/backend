from unittest.mock import patch

from fastapi.testclient import TestClient

from app.schemas.health import ServiceHealth


def test_health_check_all_services_healthy(client: TestClient):
    """Test health check when all services are healthy."""

    # Mock the external API calls to return healthy responses
    with (
        patch("app.services.routing_service.routing_service.health_check") as mock_routing,
        patch("app.services.ai_agents_service.ai_agents_service.health_check") as mock_ai,
    ):

        mock_routing.return_value = ServiceHealth(
            healthy=True, message="Routing service is responding"
        )

        mock_ai.return_value = ServiceHealth(
            healthy=True, message="AI-agents service is responding"
        )

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "commute-ai-backend"
        assert data["healthy"] is True
        assert "timestamp" in data

        # Check all dependencies are healthy
        assert data["database"]["healthy"] is True
        assert data["routing_service"]["healthy"] is True
        assert data["ai_agents_service"]["healthy"] is True


def test_health_check_database_unhealthy(client: TestClient):
    """Test health check when database is unhealthy."""

    # Mock the external API calls to return healthy responses
    with (
        patch("app.db.database.health_check") as mock_db,
        patch("app.services.routing_service.routing_service.health_check") as mock_routing,
        patch("app.services.ai_agents_service.ai_agents_service.health_check") as mock_ai,
    ):

        mock_db.return_value = ServiceHealth(
            healthy=False, message="Database connection failed: Connection refused"
        )

        mock_routing.return_value = ServiceHealth(
            healthy=True, message="Routing service is responding"
        )

        mock_ai.return_value = ServiceHealth(
            healthy=True, message="AI-agents service is responding"
        )

        response = client.get("/api/v1/health")

        assert response.status_code == 503
        data = response.json()["detail"]

        assert data["healthy"] is False
        assert data["database"]["healthy"] is False
        assert data["routing_service"]["healthy"] is True
        assert data["ai_agents_service"]["healthy"] is True


def test_health_check_routing_service_unhealthy(client: TestClient):
    """Test health check when routing service is unhealthy."""

    with (
        patch("app.services.routing_service.routing_service.health_check") as mock_routing,
        patch("app.services.ai_agents_service.ai_agents_service.health_check") as mock_ai,
    ):

        mock_routing.return_value = ServiceHealth(
            healthy=False, message="Routing service request timed out"
        )

        mock_ai.return_value = ServiceHealth(
            healthy=True, message="AI-agents service is responding"
        )

        response = client.get("/api/v1/health")

        assert response.status_code == 503
        data = response.json()["detail"]

        assert data["healthy"] is False
        assert data["database"]["healthy"] is True
        assert data["routing_service"]["healthy"] is False
        assert data["ai_agents_service"]["healthy"] is True


def test_health_check_ai_agents_service_unhealthy(client: TestClient):
    """Test health check when AI-agents service is unhealthy."""

    with (
        patch("app.services.routing_service.routing_service.health_check") as mock_routing,
        patch("app.services.ai_agents_service.ai_agents_service.health_check") as mock_ai,
    ):

        mock_routing.return_value = ServiceHealth(
            healthy=True, message="Routing service is responding"
        )

        mock_ai.return_value = ServiceHealth(
            healthy=False, message="AI-agents service returned status code: 500"
        )

        response = client.get("/api/v1/health")

        assert response.status_code == 503
        data = response.json()["detail"]

        assert data["healthy"] is False
        assert data["database"]["healthy"] is True
        assert data["routing_service"]["healthy"] is True
        assert data["ai_agents_service"]["healthy"] is False


def test_health_check_multiple_services_unhealthy(client: TestClient):
    """Test health check when multiple services are unhealthy."""

    with (
        patch("app.db.database.health_check") as mock_db,
        patch("app.services.routing_service.routing_service.health_check") as mock_routing,
        patch("app.services.ai_agents_service.ai_agents_service.health_check") as mock_ai,
    ):

        mock_db.return_value = ServiceHealth(healthy=False, message="Database connection failed")

        mock_routing.return_value = ServiceHealth(
            healthy=False, message="Routing service request timed out"
        )

        mock_ai.return_value = ServiceHealth(
            healthy=True, message="AI-agents service is responding"
        )

        response = client.get("/api/v1/health")

        assert response.status_code == 503
        data = response.json()["detail"]

        assert data["healthy"] is False
        assert data["database"]["healthy"] is False
        assert data["routing_service"]["healthy"] is False
        assert data["ai_agents_service"]["healthy"] is True


def test_health_check_response_structure(client: TestClient):
    """Test that the health check response has the correct structure."""

    with (
        patch("app.services.routing_service.routing_service.health_check") as mock_routing,
        patch("app.services.ai_agents_service.ai_agents_service.health_check") as mock_ai,
    ):

        mock_routing.return_value = ServiceHealth(
            healthy=True, message="Routing service is responding"
        )

        mock_ai.return_value = ServiceHealth(
            healthy=True, message="AI-agents service is responding"
        )

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # Check top-level structure
        required_fields = [
            "service",
            "version",
            "timestamp",
            "healthy",
            "database",
            "routing_service",
            "ai_agents_service",
        ]
        for field in required_fields:
            assert field in data

        # Check service health structure
        for service in ["database", "routing_service", "ai_agents_service"]:
            service_data = data[service]
            assert "healthy" in service_data
            assert "message" in service_data
            assert isinstance(service_data["healthy"], bool)
            assert isinstance(service_data["message"], str)
