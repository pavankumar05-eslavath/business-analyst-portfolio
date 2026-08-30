PYTHON ?= ../../.venv/bin/python

.DEFAULT_GOAL := help

.PHONY: help validate test all clean

help:  ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

validate:  ## Validate the traceability matrix against every source document
	$(PYTHON) -m tools.validate_traceability

test:  ## Run the validator under pytest
	$(PYTHON) -m pytest tests -q

all: validate test  ## Validate, then run the test suite

clean:  ## Remove Python caches
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
