-include .env
export

VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: install run serve clean test lint format type-check venv

# Create virtual environment
venv:
	python3 -m venv $(VENV)
	@echo "Virtual environment created. Activate with: source $(VENV)/bin/activate"

# Install production dependencies in venv
install: venv
	$(PIP) install .
	@echo "Dependencies installed in venv. Run 'source $(VENV)/bin/activate' to activate."

# Install development dependencies in venv
install-dev: venv
	$(PIP) install -e .
	$(PIP) install -r requirements-dev.txt
	@echo "Dev dependencies installed in venv. Run 'source $(VENV)/bin/activate' to activate."

test:
	$(PYTHON) -m pytest tests/

lint:
	ruff check .

format:
	ruff format .

type-check:
	mypy .

run:
	$(PYTHON) main.py

serve:
	$(PYTHON) -m http.server 8000

clean:
	rm -rf __pycache__
	rm -rf public/data/*.json
	rm -rf $(VENV)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete 2>/dev/null || true


