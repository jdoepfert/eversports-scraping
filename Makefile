-include .env
export

VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: install run serve clean test lint format type-check venv

# Create virtual environment
venv:
	python3 -m venv $(VENV)

# Install production dependencies in venv
install: venv
	$(PIP) install -e .

# Install development dependencies in venv
install-dev: venv
	$(PIP) install -e .
	$(PIP) install -r requirements-dev.txt

test:
	$(PYTHON) -m pytest tests/

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

type-check:
	$(PYTHON) -m mypy .

run:
	$(PYTHON) -m eversports_scraper

serve:
	$(PYTHON) -m http.server 8000

clean:
	rm -rf __pycache__
	rm -rf public/data/*.json
	rm -rf $(VENV)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete 2>/dev/null || true


