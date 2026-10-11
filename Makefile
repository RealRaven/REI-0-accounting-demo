.PHONY: up down seed demo test lint fmt law tips fixtures clean

up:
	docker compose up -d vllm qdrant postgres redis
	@echo "waiting for services..."
	@sleep 5

down:
	docker compose down

seed: law tips fixtures
	@echo "seed complete."

law:
	python scripts/seed_qdrant.py
	python scripts/index_law.py

tips:
	python scripts/index_tax_tips.py

fixtures:
	python scripts/index_fixtures.py

demo:
	python scripts/demo_run.py

test:
	pytest -q

lint:
	ruff check app tests scripts

fmt:
	ruff format app tests scripts

clean:
	rm -rf .pytest_cache .ruff_cache **/__pycache__