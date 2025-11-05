# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
make setup          # Initial project setup (create venv, install deps)
make install        # Install dependencies only
```

### Development Server
```bash
make dev            # Run development server with auto-reload on port 8000
make start          # Run production server
```

### Code Quality
```bash
make lint           # Run linting (flake8, mypy, black --check, isort --check)
make format         # Format code (black, isort)
make check          # Run all checks (lint + test)
```

### Testing
```bash
make test           # Run tests with pytest
make test-cov       # Run tests with coverage report
```

### Database Operations
```bash
make db-upgrade     # Apply database migrations
make db-downgrade   # Rollback last migration
make db-migration message="description"  # Create new migration
make db-reset       # Reset database (deletes SQLite file and recreates)
```

### Docker Operations
```bash
make docker-db-up   # Start only PostgreSQL database
make docker-up      # Start full application stack
make docker-down    # Stop all containers
make docker-build   # Build Docker image
```

## Architecture Overview

### Tech Stack
- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Authentication**: JWT tokens with bcrypt password hashing
- **External APIs**: HSL routing API, AI agents service
- **Code Quality**: Black, isort, flake8, mypy, pytest

### Project Structure
```
app/
├── api/v1/           # API versioning with FastAPI routers
│   ├── api.py        # Main API router aggregating all endpoints
│   └── endpoints/    # Individual endpoint modules (auth, users, routes, etc.)
├── core/             # Core configuration and security
│   ├── config.py     # Pydantic settings with environment variables
│   └── security.py   # JWT and password utilities
├── db/               # Database configuration
├── models/           # SQLAlchemy ORM models
├── schemas/          # Pydantic models for request/response validation
├── services/         # Business logic layer
└── utils/            # Utilities (logging, etc.)
```

### Key Components
- **Authentication**: JWT-based with username/password login
- **Route Planning**: Integration with HSL routing API for public transit
- **AI Insights**: External AI agents service for itinerary descriptions
- **User Preferences**: Stored preferences for route optimization
- **Async Support**: Full async/await pattern throughout

### Configuration
- Environment variables loaded via `.env` file
- Database URL configurable for development/production
- API keys for HSL and AI agents services
- JWT secret key auto-generated if not provided

### Testing
- pytest with async support (`pytest-asyncio`)
- Test database isolation using `conftest.py`
- Coverage reporting available via `make test-cov`
- Tests organized by feature (endpoints, services, db)

### External Integrations
- **HSL API**: Helsinki public transit routing (`api.digitransit.fi`)
- **AI Agents**: Separate service for itinerary insights (port 8001)
- **PostgreSQL**: Production database (Docker Compose setup available)

### API Structure
All endpoints under `/api/v1/` with the following main routes:
- `/health` - Health check
- `/auth` - Authentication (login/register)
- `/users` - User management
- `/users/preferences` - User preference management
- `/routes` - Route planning and search

### Development Notes
- Uses virtual environment (`venv/`) with Python 3.11+
- Alembic handles database schema migrations
- CORS enabled for development (restrict in production)
- Comprehensive logging setup via colorlog
- Code formatted to 100 character line length