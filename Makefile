SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE_FILE := infra/docker-compose.yml
ENV_FILE := .env
COMPOSE := docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE)

# Same UID/GID for api, worker and tusd, so the shared storage dir stays writable.
export AGRIDRONE_UID := $(shell id -u)
export AGRIDRONE_GID := $(shell id -g)

.PHONY: help env dirs up down logs ps test lint fmt migrate mock-data openapi openapi-check gate-a0

help: ## Show available targets
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  %-16s %s\n", $$1, $$2}'

env: $(ENV_FILE) ## Create .env from .env.example if missing

$(ENV_FILE):
	cp .env.example .env

dirs: ## Create the data/storage directories with the host user
	mkdir -p data/store/_uploads data/synthetic data/public data/samples data/work

up: env dirs ## Start the local stack and wait for healthchecks
	$(COMPOSE) up -d --wait --wait-timeout 420

down: env ## Stop the local stack
	$(COMPOSE) down --remove-orphans

logs: env ## Follow service logs
	$(COMPOSE) logs -f --tail=100

ps: env ## Show service status
	$(COMPOSE) ps

test: ## Run the test suite
	uv run pytest

lint: ## Run ruff and mypy
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy

fmt: ## Format and auto-fix code
	uv run ruff format .
	uv run ruff check --fix .

migrate: ## Apply database migrations
	uv run alembic upgrade head

mock-data: ## Generate mock data (implemented in step 02)
	@echo "Mock data generation is not implemented yet; see docs/dev-plan/02-mock-data.md."

openapi: ## Write openapi/openapi.json
	uv run agridrone openapi --out openapi/openapi.json

openapi-check: ## Fail if openapi/openapi.json is stale
	uv run agridrone openapi --check --out openapi/openapi.json

gate-a0: lint test openapi-check ## A0 gate (includes the compose smoke test)
	bash tests/smoke/cli_help.sh
	bash tests/smoke/compose_up.sh
