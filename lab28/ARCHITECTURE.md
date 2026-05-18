# Lab 28 — Architecture: 5-Layer AI Infrastructure Platform

## Hybrid Architecture

```
┌──────────────────────────────────────────────────────────────┐
│               LAYER 5: GOVERNANCE                             │
│  RBAC Manager │ PII Pipeline │ AES-256 Encryption │ Compliance│
│  (rbac.py)      (pii_pipeline.py)  (encryption.py)  (compliance)│
└──────────────────────────────────────────────────────────────┘
                              ▲
┌──────────────────────────────────────────────────────────────┐
│               LAYER 4: OPS                                    │
│  GitHub Actions CI/CD │ LangSmith │ Prometheus │ Grafana      │
│  (ci.yml, deploy.yml)   (tracing)    (:9090)      (:3000)     │
└──────────────────────────────────────────────────────────────┘
                              ▲
┌──────────────────────────────────────────────────────────────┐
│               LAYER 3: ML                                     │
│  Prefect (:4200) │ Feast/Redis (:6380) │ MLflow │ DVC         │
│  (orchestration)   (feature store)       (experiments) (data) │
└──────────────────────────────────────────────────────────────┘
                              ▲
┌──────────────────────────────────────────────────────────────┐
│               LAYER 2: DATA                                   │
│  Kafka (:9092) │ Delta Lake │ Qdrant (:6333)                  │
│  (streaming)     (storage)    (vector store)                   │
└──────────────────────────────────────────────────────────────┘
                              ▲
┌──────────────────────────────────────────────────────────────┐
│               LAYER 1: COMPUTE                                │
│  FPT Cloud AI (GPU T4/A100)                                   │
│  Qwen2.5-7B-Instruct + Vietnamese_Embedding                    │
│  API: https://mkp-api.fptcloud.com/                            │
└──────────────────────────────────────────────────────────────┘
```

## Data Flow (End-to-End)

```
1. INGEST       2. STREAM      3. PROCESS      4. STORE        5. SERVE
   scripts/01       Kafka         Prefect         Delta Lake      API Gateway
   ───────────►   data.raw   ───► flow       ───► parquet    ───► :8001
                                  │                                │
                                  ▼                                ▼
                               Feast/Redis    Qdrant           FPT Cloud AI
                               feature:*      /documents       /chat/completions
```

## Key Design Decisions

1. **Hybrid Compute**: FPT Cloud AI for GPU inference, local Docker for everything else
2. **Event-Driven**: Kafka decouples data producers from consumers
3. **GitOps**: All config in version control (docker-compose.yml, prometheus.yml, Grafana JSON)
4. **Graceful Degradation**: Circuit breakers on all external calls; fallback responses when LLM unavailable
5. **Defense in Depth**: RBAC → PII masking → Encryption → Audit logging (4 governance layers)

## Service Map

| Service | Port | Layer | Purpose |
|---------|------|-------|---------|
| API Gateway | 8001 | Integration | Single entry point; FastAPI + Prometheus |
| Kafka | 9092 | Data | Event streaming (data.raw topic) |
| Qdrant | 6333 | Data | Vector store (semantic search) |
| Redis | 6380 | ML | Feast online feature store |
| Prefect | 4200 | ML | Workflow orchestration |
| Prometheus | 9090 | Ops | Metrics collection |
| Grafana | 3000 | Ops | Dashboards + alerts |
| FPT Cloud AI | external | Compute | LLM + Embedding APIs |

## Security (Layer 5)

- **RBAC**: admin/developer/viewer roles with rate limiting
- **PII**: 6 detection rules (email, phone, CCCD, credit card, IP, passport)
- **Encryption**: AES-256-GCM for data at rest; field-level encryption
- **Compliance**: Audit log (JSONL), data retention policy, automated checks
