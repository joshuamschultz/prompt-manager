.PHONY: install test lint format type-check security clean docs help

help:
	@echo "Prompt Manager - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies"
	@echo "  make install-dev      Install with dev dependencies"
	@echo "  make install-all      Install with all extras"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests"
	@echo "  make test-cov         Run tests with coverage report"
	@echo "  make test-watch       Run tests in watch mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run all linters"
	@echo "  make format           Format code with black and ruff"
	@echo "  make type-check       Run mypy type checking"
	@echo "  make security         Run security checks"
	@echo ""
	@echo "Development:"
	@echo "  make clean            Clean generated files"
	@echo "  make docs             Generate documentation"
	@echo "  make example          Run example usage"
	@echo ""

# Setup
install:
	poetry install

install-dev:
	poetry install --with dev

install-all:
	poetry install --with dev -E all

# Testing
test:
	poetry run pytest

test-unit:
	poetry run pytest -m unit

test-integration:
	poetry run pytest -m integration

test-cov:
	poetry run pytest --cov=prompt_manager --cov-report=html --cov-report=term

test-watch:
	poetry run ptw -- -v

# Code Quality
lint:
	poetry run ruff check src/ tests/
	poetry run black --check src/ tests/

format:
	poetry run black src/ tests/ examples/
	poetry run ruff check --fix src/ tests/ examples/

type-check:
	poetry run mypy src/prompt_manager

security:
	poetry run bandit -r src/
	poetry run safety check

# Development
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docs:
	@echo "Documentation in README.md, ARCHITECTURE.md, DESIGN_DECISIONS.md"

example:
	poetry run python examples/basic_usage.py

# CI/CD
ci: lint type-check test security
	@echo "✅ All CI checks passed!"

# Build
build:
	poetry build

publish-test:
	poetry publish -r testpypi

publish:
	poetry publish

# Pre-commit
pre-commit:
	poetry run pre-commit run --all-files

pre-commit-install:
	poetry run pre-commit install
