.PHONY: install lint types test check run

install:
	uv sync

lint:
	uv run ruff format --check .
	uv run ruff check .

types:
	uv run mypy

test:
	uv run pytest

check: lint types test

run:
	uv run uvicorn apps.api.main:app --reload --port 8090
