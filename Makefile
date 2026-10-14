.PHONY: up down seed demo test lint fmt law tips fixtures clean doctor install freeze

# ----------------------------------------------------------------------
# Install
# ----------------------------------------------------------------------
install:
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt

freeze:
	python -m pip freeze > requirements.lock.txt

# ----------------------------------------------------------------------
# Lifecycle
# ----------------------------------------------------------------------
up: doctor
	docker compose up -d vllm qdrant postgres redis
	@echo "waiting for vLLM to finish loading (first run downloads the model)..."
	@for i in $$(seq 1 300); do \
		curl -sf http://localhost:8001/v1/models >/dev/null 2>&1 && { echo "  vLLM ready"; break; }; \
		[ $$((i % 20)) -eq 0 ] && echo "  ...$${i}s"; \
		sleep 1; \
	done
	@curl -sf http://localhost:8001/v1/models >/dev/null 2>&1 \
		|| { echo "vLLM did not come up — check: docker compose logs vllm"; exit 1; }
	uvicorn app.main:app --reload --port 8000

down:
	docker compose down

# ----------------------------------------------------------------------
# Pre-flight
# ----------------------------------------------------------------------
doctor:
	@test -f .env || { echo "missing .env — run: cp .env.example .env"; exit 1; }
	@python -c "import httpx, fastapi, qdrant_client, openai, rapidfuzz" 2>/dev/null \
		|| { echo "python deps missing — run: make install"; exit 1; }
	@echo "pre-flight ok"
    
# ----------------------------------------------------------------------
# Seeding
# ----------------------------------------------------------------------
seed: law tips fixtures
	@echo "seed complete."

law:
	python scripts/seed_qdrant.py
	python scripts/index_law.py

tips:
	python scripts/index_tax_tips.py

fixtures:
	python scripts/index_fixtures.py

# ----------------------------------------------------------------------
# Demo / Dev
# ----------------------------------------------------------------------
demo:
	python scripts/demo_run.py

test:
	pytest -q

lint:
	ruff check app tests scripts

fmt:
	ruff format app tests scripts

clean:
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +