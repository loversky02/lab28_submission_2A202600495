# Lab 28 Submission — 2A202600495

Full AI Infrastructure Platform — 5-Layer Architecture Demo

## Results

| Check | Result |
|-------|--------|
| Smoke Tests | **14/14 PASSED** |
| Production Readiness | **100% (17/17)** |
| Governance | **ALL VERIFIED** |

## Structure

```
lab28/
├── docker-compose.yml        # 9 services with healthchecks
├── api-gateway/              # FastAPI + Prometheus + Governance
├── scripts/                  # 10 integration scripts
├── governance/               # RBAC + PII + AES-256 + Compliance
├── monitoring/               # Prometheus + Grafana (provisioned)
├── prefect/flows/            # Kafka → Delta Lake pipeline
├── smoke-tests/              # 14 E2E smoke tests
└── fpt-cloud/                # FPT Cloud AI setup
```

## Quick Start

```bash
cd lab28
cp .env.example .env          # Add FPT_API_KEY
docker compose up -d
make data-flow                # Run full pipeline
make check                    # Smoke + verify + governance
```

## Screenshots

See `screenshots/` folder for:
- Prefect UI dashboard
- API Gateway Swagger docs
- Grafana dashboards (AI Platform Overview + Governance)
