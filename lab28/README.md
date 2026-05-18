# Lab #28 — Full AI Infrastructure Platform

**5-Layer AI Platform** từ data ingestion đến model serving với full observability + governance.

> **Compute:** FPT Cloud AI GPU (Qwen2.5-7B + Vietnamese Embedding)
> **Stack:** Kafka + Prefect + Delta Lake + Feast/Redis + Qdrant + Prometheus + Grafana

## Kiến trúc 5 Layer

```
Layer 5: GOVERNANCE  → RBAC + PII Masking + AES-256 Encryption + Compliance Audit
Layer 4: OPS         → GitHub Actions CI/CD + LangSmith + Prometheus + Grafana
Layer 3: ML          → Prefect + Feast/Redis + MLflow + DVC
Layer 2: DATA        → Kafka + Delta Lake + Qdrant Vector Store
Layer 1: COMPUTE     → FPT Cloud AI GPU (24+ models, OpenAI-compatible API)
```

## Quick Start

### 1. Setup

```bash
cd day28
cp .env.example .env       # Edit FPT_API_KEY with your key
make setup                 # Pull images, install deps
make up                    # Start 9-service platform
```

### 2. Verify Services

```bash
docker compose ps          # All services Up + Healthy
make health                # Check all endpoints
```

**Services:**
- API Gateway: http://localhost:8001/docs
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Prefect UI: http://localhost:4200
- Qdrant Dashboard: http://localhost:6333/dashboard

### 3. Run Data Pipeline

```bash
make data-flow             # Full pipeline: Demo data → Kafka → Delta → Feast → Qdrant
```

### 4. Test Chat Endpoint

```bash
curl -s -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain AI platform engineering"}' | python -m json.tool
```

### 5. Run Smoke Tests

```bash
make smoke                 # 5/5 tests should PASS
make verify                # Production readiness >80%
make governance            # Governance layer verification
```

### 6. Full Check

```bash
make check                 # Run all: smoke + verify + governance
```

## Project Structure

```
day28/
├── api-gateway/           # FastAPI gateway (Layer 2+5 integration)
│   ├── main.py            # Chat, Search, Embed endpoints + governance
│   ├── Dockerfile
│   └── requirements.txt
├── governance/            # Layer 5: Governance
│   ├── rbac.py            # Role-Based Access Control
│   ├── pii_pipeline.py    # PII Detection & Masking (6 rules)
│   ├── encryption.py      # AES-256-GCM field encryption
│   └── compliance.py      # Audit log + Retention + Checks
├── scripts/               # Integration scripts
│   ├── 01_ingest_to_kafka.py      # Data → Kafka
│   ├── 02_kafka_to_delta_local.py # Kafka → Delta Lake
│   ├── 03_delta_to_feast.py       # Delta → Feast/Redis
│   ├── 05_embed_to_qdrant.py      # Embed → Vector Store
│   ├── 06_model_update_simulate.py # MLflow + DVC simulation
│   ├── 07_governance_check.py     # Governance verification
│   ├── 08_generate_demo_data.py   # 50 records (VN + EN)
│   ├── 09_verify_observability.py # Prometheus + LangSmith check
│   └── production_readiness_check.py  # 15-point checklist
├── smoke-tests/           # 5 E2E smoke tests
│   └── test_e2e.py
├── monitoring/            # Layer 4: Observability
│   ├── prometheus.yml
│   └── grafana/
│       ├── provisioning/  # Auto-configured datasources + dashboards
│       └── dashboards/    # Platform Overview + Governance dashboards
├── prefect/flows/         # Layer 3: Pipeline orchestration
│   └── kafka_to_delta.py
├── fpt-cloud/             # Layer 1: FPT Cloud AI setup guide
├── .github/workflows/     # CI/CD
│   ├── ci.yml             # Smoke tests on PR
│   └── deploy.yml         # Deploy on main
├── docker-compose.yml     # 9 services with healthchecks
├── Makefile               # Orchestration (setup, up, smoke, verify, demo)
├── .env.example           # Environment template
├── ARCHITECTURE.md        # 5-layer architecture doc
├── DEMO_SCRIPT.md         # 15-minute demo script
└── README.md
```

## API Endpoints

| Method | Path | Description | Governance |
|--------|------|-------------|-----------|
| GET | `/health` | Health check with layer status | — |
| POST | `/api/v1/chat` | Chat completion (RAG) | RBAC + PII masking |
| POST | `/api/v1/search` | Vector search only | RBAC |
| POST | `/api/v1/embed` | Text embeddings | Rate limiting |
| GET | `/metrics` | Prometheus metrics | — |
| GET | `/metrics-summary` | Circuit breaker state | RBAC |
| GET | `/admin` | Returns 403 (security test) | RBAC enforced |

## Production Readiness Target

| Category | Checks | Target |
|----------|--------|--------|
| Layer 1 — Compute | FPT API key + LLM reachable | 2/2 |
| Layer 2 — Data | Kafka + Qdrant + collection | 3/3 |
| Layer 3 — ML | Prefect + Redis + Features | 3/3 |
| Layer 4 — Ops | Prometheus + Grafana + Metrics | 3/3 |
| Layer 5 — Governance | RBAC + PII + Circuit breaker | 4/4 |
| **Total** | **15 checks** | **>80% = 12/15** |

## Makefile Commands

```bash
make help        # Show all commands
make up          # Start platform
make data-flow   # Run full data pipeline
make smoke       # Run 5 smoke tests
make verify      # Production readiness check
make governance  # Governance verification
make check       # All checks
make demo        # Full demo sequence
make load-test   # Send 20 concurrent requests
make clean       # Clean local artifacts
```

## Submission Checklist

- [ ] `docker compose ps` — all services Up
- [ ] `make data-flow` — pipeline completes
- [ ] `curl http://localhost:8001/api/v1/chat` — LLM responds
- [ ] `make smoke` — 5/5 PASSED
- [ ] `make verify` — score >= 80%
- [ ] `make governance` — ALL VERIFIED
- [ ] Grafana dashboard has metrics
- [ ] Demo script rehearsed once
