.PHONY: install api web test lint bench check

install:
	pip install -r backend/requirements-dev.txt
	cd frontend && npm install

api:
	cd backend && uvicorn app.main:app --reload

web:
	cd frontend && npm run dev

lint:
	cd backend && ruff check app tests

test:
	cd backend && pytest -q
	cd frontend && npm test

bench:
	cd backend && python -m app.eval.cli --corpus ../samples/corpus --dataset ../samples/eval.jsonl --failures

check: lint test bench
	cd frontend && npm run typecheck
