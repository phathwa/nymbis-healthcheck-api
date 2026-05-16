.PHONY: install run test lint format check clean

install:
	python -m pip install -r requirements.txt

run:
	python app.py

test:
	python -m pytest

lint:
	python -m flake8 .

format:
	python -m black --line-length 79 .

check: lint test

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -f .coverage
	rm -rf htmlcov