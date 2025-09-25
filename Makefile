# Commute.ai Backend Makefile

.PHONY: help install dev start test clean lint format check docker-build docker-up docker-down setup

# Default target
help:
	@echo "Available commands:"
	@echo "  setup      - Initial project setup (create venv, install deps)"
	@echo "  install    - Install dependencies"
	@echo "  dev        - Run development server with auto-reload"
	@echo "  start      - Run production server"
	@echo "  test       - Run tests"
	@echo "  lint       - Run linting"
	@echo "  format     - Format code with black"
	@echo "  check      - Run all checks (lint + test)"
	@echo "  clean      - Clean up generated files"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-up  - Start with Docker Compose"
	@echo "  docker-down - Stop Docker Compose"

# Variables
PYTHON := python3
VENV := venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python
PORT := 8000
HOST := 0.0.0.0

# Initial setup
setup:
	@echo "🚀 Setting up Commute.ai backend..."
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ Setup complete! Run 'make dev' to start development server"

# Install dependencies
install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# Development server with auto-reload
dev:
	@echo "🔄 Starting development server on http://$(HOST):$(PORT)"
	$(PYTHON_VENV) -m uvicorn app.main:app --reload --host $(HOST) --port $(PORT)

# Production server
start:
	@echo "🚀 Starting production server on http://$(HOST):$(PORT)"
	$(PYTHON_VENV) -m uvicorn app.main:app --host $(HOST) --port $(PORT)

# Run tests
test:
	@echo "🧪 Running tests..."
	$(PYTHON_VENV) -m pytest tests/ -v

# Run tests with coverage
test-cov:
	@echo "🧪 Running tests with coverage..."
	$(PYTHON_VENV) -m pytest tests/ --cov=app --cov-report=html --cov-report=term

# Lint code
lint:
	@echo "🔍 Linting code..."
	$(PYTHON_VENV) -m flake8 app/ tests/
	$(PYTHON_VENV) -m mypy app/

# Format code
format:
	@echo "✨ Formatting code..."
	$(PYTHON_VENV) -m black app/ tests/
	$(PYTHON_VENV) -m isort app/ tests/

# Run all checks
check: lint test
	@echo "✅ All checks passed!"

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/

# Database commands
db-upgrade:
	@echo "⬆️ Upgrading database..."
	$(PYTHON_VENV) -m alembic upgrade head

db-downgrade:
	@echo "⬇️ Downgrading database..."
	$(PYTHON_VENV) -m alembic downgrade -1

db-migration:
	@echo "📝 Creating new migration..."
	$(PYTHON_VENV) -m alembic revision --autogenerate -m "$(message)"

db-reset:
	@echo "🔄 Resetting database..."
	rm -f commute_ai.db
	$(PYTHON_VENV) -m alembic upgrade head

# Docker commands
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t commute-ai-backend .

docker-up:
	@echo "🐳 Starting with Docker Compose..."
	docker compose up -d

docker-down:
	@echo "🐳 Stopping Docker Compose..."
	docker compose down

docker-logs:
	@echo "📋 Showing Docker logs..."
	docker compose logs -f

# Create requirements files
freeze:
	@echo "📦 Updating requirements.txt..."
	$(PIP) freeze > requirements.txt
