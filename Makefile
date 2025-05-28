.PHONY: help install install-dev lint format check test clean setup-dev

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e ".[dev]"

setup-dev: ## Setup development environment (install deps + pre-commit)
	./scripts/setup-dev.sh

lint: ## Run Ruff linter
	ruff check .

lint-fix: ## Run Ruff linter with auto-fix
	ruff check --fix .

format: ## Run Ruff formatter
	ruff format .

check: ## Run all checks (lint + format)
	ruff check . && ruff format --check .

pre-commit: ## Run pre-commit on all files
	pre-commit run --all-files

pre-commit-install: ## Install pre-commit hooks
	pre-commit install

clean: ## Clean up cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run: ## Run the Streamlit app
	streamlit run chatbot/app.py
