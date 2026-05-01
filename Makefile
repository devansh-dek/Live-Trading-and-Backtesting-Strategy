.PHONY: install test lint backtest walkforward fetch-data report live verify clean

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	ruff check src tests config scripts run_*.py

backtest:
	python run_backtest.py

walkforward:
	python run_walkforward.py

fetch-data:
	python scripts/fetch_data.py

report:
	python run_backtest.py --report

live:
	python run_live.py

verify:
	python scripts/verify_setup.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage
