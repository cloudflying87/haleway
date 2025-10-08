# Makefile for haleway
# Run 'make help' to see all available commands

.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development Commands
.PHONY: run
run: ## Run development server
	python manage.py runserver

.PHONY: migrate
migrate: ## Run database migrations
	python manage.py makemigrations
	python manage.py migrate

.PHONY: shell
shell: ## Django shell with shell_plus
	python manage.py shell_plus || python manage.py shell

.PHONY: test
test: ## Run tests
	python manage.py test

.PHONY: coverage
coverage: ## Run tests with coverage
	coverage run --source='.' manage.py test
	coverage report
	coverage html

# Code Quality (using modern tools)
.PHONY: format
format: ## Format code with ruff
	ruff format .
	ruff check --fix .

.PHONY: lint
lint: ## Run linting checks with ruff
	ruff check .
	ruff format --check .

.PHONY: type-check
type-check: ## Run type checking with mypy
	mypy apps/ config/

.PHONY: security
security: ## Run security checks with bandit
	bandit -r apps/ -c pyproject.toml

.PHONY: quality
quality: lint type-check security ## Run all code quality checks

# Database Commands
.PHONY: dbshell
dbshell: ## Access database shell
	python manage.py dbshell

.PHONY: reset-db
reset-db: ## Reset database (CAUTION: destroys all data)
	python manage.py flush --no-input
	python manage.py migrate

# Static Files
.PHONY: static
static: ## Collect static files
	python manage.py collectstatic --no-input

# Docker Commands (Production)
.PHONY: docker-build
docker-build: ## Build Docker containers
	docker compose build

.PHONY: docker-up
docker-up: ## Start Docker containers
	docker compose up -d

.PHONY: docker-down
docker-down: ## Stop Docker containers
	docker compose down

.PHONY: docker-logs
docker-logs: ## View Docker logs
	docker compose logs -f

.PHONY: docker-shell
docker-shell: ## Access web container shell
	docker compose exec web bash

# Production Deployment
.PHONY: deploy
deploy: ## Deploy to production
	./build.sh -r -d $$(date +%Y%m%d)

.PHONY: backup
backup: ## Backup database
	./build.sh -b -d $$(date +%Y%m%d)

.PHONY: restore
restore: ## Restore database (requires DATE)
	@if [ -z "$(DATE)" ]; then echo "Usage: make restore DATE=YYYYMMDD"; exit 1; fi
	./build.sh -o -d $(DATE)

# Initial Setup
.PHONY: install
install: ## Install dependencies (using uv for speed)
	@command -v uv >/dev/null 2>&1 && uv pip install -r requirements/development.txt || pip install -r requirements/development.txt
	@echo "💡 Tip: Install uv for 10-100x faster installs: pip install uv"

.PHONY: install-uv
install-uv: ## Install uv package manager
	pip install uv

.PHONY: setup
setup: install migrate ## Initial project setup
	python manage.py createsuperuser
	pre-commit install
	@echo "✅ Setup complete! Run 'make run' to start development server."

# Cleanup
.PHONY: clean
clean: ## Clean temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/

# Help Commands
.PHONY: urls
urls: ## Show all URL patterns
	python manage.py show_urls

.PHONY: check
check: ## Run Django system checks
	python manage.py check --deploy

.PHONY: health
health: ## Check application health endpoints
	@echo "Checking health endpoints..."
	@curl -f http://localhost:8000/health/ || echo "❌ Health check failed (make sure server is running)"

.PHONY: check-migrations
check-migrations: ## Lint Django migrations for unsafe operations
	python manage.py lintmigrations

.PHONY: todo
todo: ## Find all TODO comments
	@grep -r "TODO" apps/ templates/ --exclude-dir=__pycache__ || echo "No TODOs found"