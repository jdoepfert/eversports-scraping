-include .env
export

.PHONY: install run serve clean test lint format type-check

test:
	pytest tests/

lint:
	ruff check .

format:
	ruff format .

type-check:
	mypy .

install:
	pip install .

install-dev:
	pip install -e .
	pip install -r requirements-dev.txt

run:
	python main.py

serve:
	python -m http.server 8000

clean:
	rm -rf __pycache__
	rm -rf public/data/*.json


