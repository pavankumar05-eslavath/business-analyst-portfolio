PYTHON ?= ../../.venv/bin/python

.DEFAULT_GOAL := help

.PHONY: help analyse build all test lint clean

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

analyse:  ## Print the analysis and write outputs/analysis.txt
	$(PYTHON) -m src.run analyse

build:  ## Write outputs/unit_economics.xlsx with live formulas
	$(PYTHON) -m src.run build

all: analyse build  ## Run the analysis and build the workbook

test:  ## Run the test suite, including the Excel-vs-Python cross-check
	$(PYTHON) -m pytest tests -q

lint:  ## Lint
	$(PYTHON) -m ruff check .

clean:  ## Remove generated outputs and caches
	rm -rf outputs
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache
