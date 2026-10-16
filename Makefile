# Load .env when present.
ifneq ("$(wildcard .env)","")
    include .env
    export
endif

.PHONY: install run run.worker run.beat format ruff-format ruff-check ruff-fix mypy lint check test test-unit test-integration pre-commit pre-commit-install migration migrate migration-check docker-up docker-down logs clean

install:
	uv sync --all-groups

run:
	uv run uvicorn crypto_prices.main:app --reload --host 0.0.0.0 --port 8000

run.worker:
	uv run celery -A crypto_prices.tasks.celery_app:celery_app worker --loglevel=INFO

run.beat:
	uv run celery -A crypto_prices.tasks.celery_app:celery_app beat --loglevel=INFO

format:
	uv run ruff format .
	uv run ruff check --fix .

ruff-format:
	uv run ruff format .

ruff-check:
	uv run ruff check .

ruff-fix:
	uv run ruff check --fix .

mypy:
	uv run mypy src tests

lint: ruff-check mypy

check:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src tests

test:
	uv run pytest

test-unit:
	uv run pytest tests/unit

pre-commit:
	uv run pre-commit run --all-files

pre-commit-install:
	uv run pre-commit install

migration:
	uv run alembic revision --autogenerate -m "$(message)"

migrate:
	uv run alembic upgrade head

migration-check:
	uv run alembic check

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

logs:
	docker compose logs -f --tail=100

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	find . -type d -name .mypy_cache -prune -exec rm -rf {} +
