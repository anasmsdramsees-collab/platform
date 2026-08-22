# SYLTRA Adaptive Edge Platform — developer commands (spec §9).
# Every target is documented in README.md. Targets whose subsystems arrive in a
# later phase fail fast with a clear message so target names are stable from day one.

SHELL := /bin/bash
COMPOSE := docker compose

.PHONY: hub bootstrap config-check up down reset-demo seed simulate simulate-list contracts tokens contrast console observe migrate migrate-status \
        test test-integration test-e2e test-safety lint security coverage demo \
        logs health

bootstrap: ## Install development prerequisites (pinned Python + workspace deps)
	uv python install 3.12
	uv sync --all-packages
	@echo "✔ bootstrap complete — try 'make lint' and 'make test'"

config-check: ## Validate configuration and environment
	./infrastructure/scripts/config-check.sh

up: ## Start the development platform (infra containers; SYLTRA services join in Phase 1)
	$(COMPOSE) up -d
	$(COMPOSE) ps

down: ## Stop the development platform
	$(COMPOSE) down

reset-demo: ## Reset demo data only — never user data
	./infrastructure/scripts/reset-demo.sh

seed: ## Load deterministic demo fixtures into the running stack
	uv run syltra-simulate --nats normal_day

simulate: ## Run the deterministic smart-home simulation (no infrastructure needed)
	uv run syltra-simulate

simulate-list: ## List available simulator scenarios
	uv run syltra-simulate --list

contracts: ## Regenerate every contract artifact (schemas, examples, OpenAPI)
	uv run python -m syltra_contracts.schema_export
	uv run python -m syltra_contracts.example_export
	uv run python -m syltra_api_gateway.openapi_export

console: ## Run the console and component catalogue locally (dev token printed)
	uv run python -m syltra_api_gateway.devserver

hub: ## Run the hub against a real Home Assistant (see docs/HUB_ON_A_MINI_PC.md)
	uv run python -m syltra_api_gateway.hub

tokens: ## Regenerate the design-system CSS from tokens.json (guidelines §24)
	uv run python infrastructure/scripts/build_tokens.py

contrast: ## Report the WCAG contrast of every token pair, both themes
	uv run python -m syltra_design_tokens

migrate: ## Apply database migrations to the configured database
	uv run alembic upgrade head

migrate-status: ## Show the current migration revision
	uv run alembic current

test: ## Run unit and contract tests
	# Spec §9 scopes this to unit and contract tests; integration tests, which
	# need the running stack and its credentials, have their own target.
	uv run pytest libs services apps simulator home-assistant

test-integration: ## Run integration tests (mock Home Assistant boundary + services)
	# Credentials live in .env only, never in checked-in test files (spec §25.3).
	# Tests that need them skip with a clear reason when .env is absent.
	@set -a; [ -f .env ] && . ./.env; set +a; uv run pytest tests/integration

test-e2e: ## Run end-to-end tests (arrives in Phase 5+; requires the full stack)
	@if [ -z "$$(find tests/end_to_end -name 'test_*.py' -print -quit)" ]; then \
		echo "test-e2e arrives in Phase 5 (full recommendation→action chain)."; exit 1; \
	fi
	uv run pytest tests/end_to_end

test-safety: ## Run all safety scenarios (deterministic; must pass without AI services)
	@set -a; [ -f .env ] && . ./.env; set +a; \
	uv run pytest -m safety

lint: ## Format check, lint, and type checks
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy

security: ## Security checks (bandit; dependency audit runs in CI)
	uv run bandit -q -r libs services simulator -x "*/tests/*"
	@echo "✔ bandit clean (pip-audit dependency scan runs in CI)"

coverage: ## Coverage report (safety modules require full branch coverage)
	uv run coverage run -m pytest
	uv run coverage report

demo: ## Start the platform and run the deterministic demo against it
	$(MAKE) up
	@echo "waiting for services to become healthy…" && sleep 10
	$(MAKE) seed
	$(MAKE) health

observe: ## Start Prometheus and Grafana (spec §29 dashboard) on 127.0.0.1:3001
	@grep -q '^GRAFANA_ADMIN_PASSWORD=.\+' .env 2>/dev/null || { \
		echo "Set GRAFANA_ADMIN_PASSWORD in .env first — a dashboard of a household's"; \
		echo "behavioural history does not ship with a default password."; exit 1; }
	$(COMPOSE) --profile observability up -d prometheus grafana
	@echo "✔ dashboard: http://127.0.0.1:3001  (SYLTRA — hub overview)"

logs: ## Tail structured service logs
	$(COMPOSE) logs -f --tail=100

backup: ## Create an encrypted household backup (spec §22 Phase 8)
	uv run python infrastructure/scripts/backup.py create \
		--home-id $${SYLTRA_HOME_ID:-home_dev_001} \
		--out backups/syltra-$$(date +%Y%m%d-%H%M%S).syltrabk

backup-info: ## Read a backup manifest without the passphrase (FILE=...)
	uv run python infrastructure/scripts/backup.py info $(FILE)

restore: ## Verify and restore an encrypted backup (FILE=...)
	uv run python infrastructure/scripts/backup.py restore $(FILE)

diagnostics: ## Build a redacted support bundle (no household data)
	@mkdir -p diagnostics
	uv run python infrastructure/scripts/backup.py diagnostics \
		--out diagnostics/syltra-$$(date +%Y%m%d-%H%M%S).json

health: ## Show service health
	$(COMPOSE) ps
