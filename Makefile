.PHONY: run lint format test

run:
	uv run uvicorn habit_homepage.main:app --reload

lint:
	uv run ruff check .

format:
	uv run ruff format .

check:
	uv run mypy .

test:
	uv run pytest
