# HOS Trip Planner — backend developer commands.
# Most targets run inside Docker so no local Python/venv is required.

.PHONY: help build up run down migrate makemigrations shell test test-engine logs

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

build: ## Build the web image
	docker compose build

up run: ## Start Postgres + web (http://localhost:8000)
	docker compose up --build

down: ## Stop and remove containers + volumes
	docker compose down -v

migrate: ## Apply migrations
	docker compose run --rm web python manage.py migrate

makemigrations: ## Generate migrations
	docker compose run --rm web python manage.py makemigrations

shell: ## Django shell
	docker compose run --rm web python manage.py shell

logs: ## Tail web logs
	docker compose logs -f web

test: ## Run the full suite (engine + API) via pytest
	docker compose run --rm web sh -c "pip install -q -r requirements-dev.txt && pytest -q"

test-engine: ## Run the dependency-free engine tests locally (no Docker needed)
	python3 -m unittest hos.tests.test_engine -v
