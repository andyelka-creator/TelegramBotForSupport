.PHONY: install-dev precommit-install lint typecheck test test-unit test-integration test-contract test-e2e

install-dev:
	pip install -e ".[dev]"

precommit-install:
	pre-commit install

lint:
	ruff check .
	ruff format --check .

typecheck:
	mypy app tests

test:
	pytest -q -m "not e2e"

test-unit:
	pytest -q -m unit

test-integration:
	pytest -q -m integration

test-contract:
	pytest -q -m contract

test-e2e:
	E2E_ENABLE=1 pytest -q -m e2e
