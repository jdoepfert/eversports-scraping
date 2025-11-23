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
	rm -rf docs/data/*.json

deploy:
	git add docs/data/availability.json docs/data/report.json docs/index.html
	@if ! git diff --quiet || ! git diff --staged --quiet; then \
		git commit -m "[BOT] Update availability"; \
		git push; \
	else \
		echo "No changes to commit."; \
	fi
