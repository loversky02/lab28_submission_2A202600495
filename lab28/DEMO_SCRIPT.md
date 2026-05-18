# Lab 28 — Milestone 3 Demo Script (15 phút)

## Chuẩn bị

```bash
# Terminal 1: Docker logs
docker compose logs -f api-gateway

# Terminal 2: Demo commands
cd /home/loversky/Desktop/code/vinai/day28
```

---

## Phần 1 — Architecture Overview (2 phút)

**Mở:** `ARCHITECTURE.md`

Giải thích 5-layer architecture:
1. **Layer 1 — Compute**: FPT Cloud AI GPU (Qwen2.5-7B, 24+ models)
2. **Layer 2 — Data**: Kafka streaming + Delta Lake + Qdrant vector store
3. **Layer 3 — ML**: Prefect orchestration + Feast feature store + MLflow + DVC
4. **Layer 4 — Ops**: Prometheus/Grafana + LangSmith + GitHub Actions CI/CD
5. **Layer 5 — Governance**: RBAC + PII masking + AES-256 encryption + Compliance audit

**Nói:** "Platform này demo full stack AI infrastructure — từ data ingestion đến model serving với observability và governance."

---

## Phần 2 — Live Demo: Happy Path (5 phút)

### Bước 1: Infrastructure check
```bash
docker compose ps
# → Tất cả 9 services Up + Healthy
```

### Bước 2: Health check
```bash
curl -s http://localhost:8001/health | python -m json.tool
# → Hiển thị 5 layers status
```

### Bước 3: Ingest data → Kafka
```bash
python scripts/08_generate_demo_data.py
python scripts/01_ingest_to_kafka.py
# → 50 records (Việt + Anh) vào Kafka topic data.raw
```

### Bước 4: Pipeline Kafka → Delta → Feast
```bash
python scripts/02_kafka_to_delta_local.py
python scripts/03_delta_to_feast.py
# → Data flow qua Kafka → Delta Lake → Redis (Feast)
```

### Bước 5: Gọi API Gateway → LLM inference
```bash
curl -s -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain AI platform engineering in 3 sentences"}' \
  | python -m json.tool
# → Response từ FPT Cloud AI (Qwen2.5-7B) với latency < 2s
```

**Nói:** "Đây là end-to-end flow: data từ Kafka qua pipeline, lưu vào Delta Lake và Feast, rồi API Gateway gọi FPT Cloud AI để inference."

---

## Phần 3 — Error Scenario Demo (3 phút)

### Bước 1: Test graceful degradation
```bash
# Gửi request không có API key — vẫn có fallback response
curl -s -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}' | python -m json.tool
# → Response: "[Demo mode] You asked: test..."
```

### Bước 2: Test RBAC
```bash
# Admin endpoint bị chặn
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8001/admin
# → 403 Forbidden
```

### Bước 3: Test PII masking
```bash
curl -s -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "My email is test@example.com and phone 0987654321"}' \
  | python -m json.tool
# → PII bị mask thành ***REDACTED***
```

### Bước 4: Circuit breaker
```bash
curl -s http://localhost:8001/metrics-summary | python -m json.tool
# → Hiển thị circuit breaker state cho llm, embed, qdrant
```

---

## Phần 4 — Observability Walkthrough (3 phút)

### Mở Grafana
```bash
# http://localhost:3000 (admin/admin)
# Dashboards: "AI Platform Overview" + "Layer 5 — Governance"
```

### Mở Prometheus
```bash
# http://localhost:9090
# Query: rate(http_requests_total[1m])
# Query: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1m]))
```

### Mở Prefect
```bash
# http://localhost:4200
# Flow: "Kafka to Delta Pipeline"
```

### Load test nhỏ
```bash
make load-test
# → 20 concurrent requests → metrics hiển thị trên Grafana
```

**Nói:** "Observability stack cho phép monitor toàn bộ platform — từ request rate, latency, error rate đến circuit breaker status."

---

## Phần 5 — Q&A (2 phút)

**Chuẩn bị câu trả lời:**

1. **"Tại sao dùng Kafka thay vì gọi trực tiếp?"**
   → Decoupling: producer và consumer độc lập. Replay: có thể đọc lại events. Buffer: chống back-pressure.

2. **"Circuit breaker implement ở đâu?"**
   → API Gateway middleware. Sau 3 lần fail liên tiếp → circuit opens (30s timeout). Có graceful degradation.

3. **"Nếu FPT Cloud ngắt kết nối thì sao?"**
   → Fallback mode: API Gateway trả về response mẫu thay vì crash. Circuit breaker bảo vệ hệ thống.

4. **"Production readiness score hiện tại?"**
   → Chạy `make verify` để show real-time score >80%.

5. **"Governance layer hoạt động thế nào?"**
   → 4 components: RBAC (phân quyền), PII pipeline (phát hiện + mask), Encryption (AES-256-GCM), Compliance (audit log + retention policy).

---

## Kết thúc demo

```bash
# Show final verification
make check
# → Smoke tests: 5/5 PASSED
# → Production readiness: >80%
# → Governance: ALL VERIFIED
```
