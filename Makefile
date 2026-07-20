.PHONY: install dev-install test test-unit test-integration lint format \
        db-up db-down migrate migration-create clean

install:
	pip install -e ".[dev]"

dev-install:
	pip install -e ".[dev,ml]"

db-up:
	docker compose up -d

db-down:
	docker compose down

migrate:
	alembic upgrade head

migration-create:
	alembic revision --autogenerate -m "$(msg)"

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

lint:
	ruff check agent_monitor/ demo_advisory/ tests/

format:
	ruff format agent_monitor/ demo_advisory/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
