.PHONY: install install-dev run test lint init-db

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

test:
	PYTHONPATH=. pytest

lint:
	ruff check app tests
	black --check app tests

init-db:
	PYTHONPATH=. python scripts/init_db.py

