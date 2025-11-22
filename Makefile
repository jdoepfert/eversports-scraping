.PHONY: install run serve clean

install:
	pip install -r requirements.txt

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
