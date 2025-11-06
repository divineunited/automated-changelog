.PHONY: help setup clean test test-cov lint format run-init run-generate

PYTHON_VERSION ?= 3.12
VENV := .venv

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup:  ## Create virtual environment and install dependencies using uv
	uv venv --python $(PYTHON_VERSION)
	uv pip install -e ".[dev]"
	@echo ""
	@echo "Setup complete! Activate the virtual environment with:"
	@echo "  source .venv/bin/activate"

clean:  ## Clean build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .ruff_cache/
	rm -rf $(VENV)
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

test:  ## Run tests
	uv run pytest

lint:  ## Run linters (ruff and mypy)
	uv run ruff check src/ tests/
	uv run mypy src/

format:  ## Format code with black and ruff
	uv run black src/ tests/
	uv run ruff check --fix src/ tests/

run-init:  ## Run the init command (creates config file)
	uv run automated-changelog init

run-generate:  ## Run the generate command
	uv run automated-changelog generate

run-generate-dry:  ## Run generate in dry-run mode
	uv run automated-changelog generate --dry-run

run-generate-dry-no-ssl:  ## Run generate in dry-run mode with SSL verification disabled
	SSL_VERIFY=false uv run automated-changelog generate --dry-run
