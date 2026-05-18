# Lab 28 — Full AI Infrastructure Platform
# 5-layer platform orchestration

.PHONY: help setup up down ps logs build clean smoke verify demo

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	 awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Pull images and create directories
	@echo "=== Setting up Lab 28 Platform ==="
	mkdir -p delta-lake/raw outputs mlruns
	cp -n .env.example .env 2>/dev/null || true
	docker compose pull
	pip install -q -r requirements.txt
	@echo "Setup complete. Edit .env with your FPT_API_KEY."

up: ## Start all platform services
	docker compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 10
	docker compose ps

down: ## Stop all services (preserves data)
	docker compose down

down-clean: ## Stop services and remove volumes
	docker compose down -v
	rm -rf delta-lake/raw/* outputs/*.json

ps: ## Show service status
	docker compose ps

logs: ## Follow all service logs
	docker compose logs -f

build: ## Rebuild API gateway
	docker compose build api-gateway
	docker compose up -d api-gateway

# ── Data Pipeline ──────────────────────────────────────────

demo-data: ## Generate demo dataset
	python scripts/08_generate_demo_data.py

ingest: ## Ingest data into Kafka
	python scripts/01_ingest_to_kafka.py

pipeline: ## Run full data pipeline (Kafka → Delta → Feast)
	python scripts/02_kafka_to_delta_local.py
	python scripts/03_delta_to_feast.py

embed: ## Embed data into Qdrant vector store
	python scripts/05_embed_to_qdrant.py

data-flow: demo-data ingest pipeline embed ## Run complete data flow

# ── Testing ────────────────────────────────────────────────

smoke: ## Run smoke tests
	pytest smoke-tests/ -v

smoke-fast: ## Run smoke tests (first 2 only)
	pytest smoke-tests/test_e2e.py::TestHappyPath -v

verify: ## Run production readiness check
	python scripts/production_readiness_check.py

governance: ## Verify governance layer
	python scripts/07_governance_check.py

check: smoke verify governance ## Run all checks

# ── Demo ───────────────────────────────────────────────────

demo: ## Run full demo sequence
	@echo "=== Lab 28 — Full Platform Demo ==="
	@echo "1. Infrastructure check..."
	docker compose ps
	@echo ""
	@echo "2. Health check..."
	curl -s http://localhost:8001/health | python -m json.tool
	@echo ""
	@echo "3. Data pipeline..."
	python scripts/08_generate_demo_data.py
	python scripts/01_ingest_to_kafka.py
	@echo ""
	@echo "4. Chat inference..."
	curl -s -X POST http://localhost:8001/api/v1/chat \
	  -H "Content-Type: application/json" \
	  -d '{"query": "What is AI platform engineering?"}' | python -m json.tool
	@echo ""
	@echo "5. Smoke tests..."
	pytest smoke-tests/ -v
	@echo ""
	@echo "6. Production readiness..."
	python scripts/production_readiness_check.py

load-test: ## Run light load test
	@for i in $$(seq 1 20); do \
	  curl -s -X POST http://localhost:8001/api/v1/chat \
	    -d "{\"query\": \"load test $$i\"}" & \
	done; wait; echo "20 requests sent"

# ── Utilities ───────────────────────────────────────────────

health: ## Check all service health
	@echo "API Gateway: $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8001/health)"
	@echo "Prometheus: $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:9090/-/healthy)"
	@echo "Grafana:    $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/api/health -u admin:admin)"
	@echo "Qdrant:     $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:6333/healthz)"
	@echo "Prefect:    $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:4200/api/health)"

clean: ## Clean local artifacts (preserves Docker volumes)
	rm -rf delta-lake/raw/* outputs/*.json mlruns/*
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
