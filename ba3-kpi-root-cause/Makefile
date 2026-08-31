PYTHON ?= ../../.venv/bin/python

.DEFAULT_GOAL := help

.PHONY: help data analyse all test lint clean

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

data:  ## Generate the ticket dataset (queue simulation)
	$(PYTHON) -m data.generate_tickets

analyse: data  ## Run the full root-cause analysis
	$(PYTHON) -m src.run

all: analyse  ## Generate data and run the analysis

test: data  ## Run the test suite
	$(PYTHON) -m pytest tests -q

lint:  ## Lint
	$(PYTHON) -m ruff check .

clean:  ## Remove generated data, outputs and caches
	rm -rf outputs data/tickets.parquet
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache
