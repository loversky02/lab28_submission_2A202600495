# Lab 28 — 5 Câu Hỏi Nộp Bài

## Câu 1: Trade-offs trong thiết kế kiến trúc AI Platform

**Cân bằng giữa Performance, Reliability, và Maintainability:**

| Yếu tố | Quyết định | Trade-off |
|--------|-----------|-----------|
| **Performance** | FPT Cloud AI GPU (thay vì local LLM) | Độ trễ mạng (~500ms) đánh đổi lấy khả năng inference 24+ models không cần GPU local |
| **Reliability** | Circuit Breaker pattern trên tất cả external calls | 3 lần fail → circuit mở 30s, graceful degradation thay vì crash |
| **Maintainability** | GitOps config (docker-compose.yml + prometheus.yml + Grafana JSON) | Toàn bộ config trong version control, tái tạo môi trường trong 1 lệnh `docker compose up -d` |

**Kiến trúc 5-layer separation** đảm bảo mỗi layer có thể thay đổi độc lập mà không ảnh hưởng layer khác.

---

## Câu 2: Xử lý ngắt kết nối giữa Local và Cloud (FPT Cloud AI)

**Cơ chế fallback 3 tầng:**

1. **Circuit Breaker**: Sau 3 lần fail liên tiếp → circuit opens (30s timeout). Các request tiếp theo nhận HTTP 503 ngay lập tức thay vì timeout.
2. **Graceful Degradation**: Khi không có API key → API Gateway vẫn trả về response mẫu `[Demo mode] You asked: ...` thay vì crash.
3. **State Recovery**: Circuit tự động half-open sau 30s để test lại kết nối. Nếu thành công → đóng circuit và hoạt động bình thường.

```
FPT Cloud AI unavailable?
  → Circuit breaker opens
  → GET /metrics-summary hiển thị trạng thái circuit
  → Sau 30s tự động retry
  → Nếu FPT quay lại → tự phục hồi
```

---

## Câu 3: Event-Driven Architecture với Kafka

**Kafka decouple các components như thế nào:**

- **Producer độc lập với Consumer**: Scripts ingest data vào Kafka topic `data.raw` mà không cần biết ai sẽ consume. Consumer (Delta Lake, Prefect) đọc từ topic khi sẵn sàng.
- **Replay capability**: Events được lưu trong Kafka, có thể replay khi cần debug hoặc backfill dữ liệu.
- **Buffer chống back-pressure**: Nếu Delta Lake xử lý chậm, Kafka giữ events (không bị mất data).
- **Multi-consumer**: Cùng một topic có thể được consume bởi nhiều service khác nhau (Delta Lake, monitoring, audit log).

---

## Câu 4: Observability Implementation

**3 pillars of observability:**

| Pillar | Tool | Chi tiết |
|--------|------|---------|
| **Metrics** | Prometheus + Grafana | `prometheus_fastapi_instrumentator` tự động expose HTTP metrics (rate, latency, errors). Prometheus scrape mỗi 15s. 5 scrape jobs với layer labels. |
| **Dashboards** | Grafana (auto-provisioned) | 2 dashboards: "AI Platform Overview" (API rate, P95 latency, error rate) + "Layer 5 Governance" (RBAC denials, PII masking rate, circuit breaker status) |
| **Traces** | LangSmith (optional) | Mỗi chat request được trace với inputs (query + context) và outputs (answer), project = `lab28-platform` |

**Alert Pipeline**: Prometheus rules → Grafana alerts → notification channels (cấu hình sẵn trong provisioning).

---

## Câu 5: Graceful Degradation khi Service Crash

**Kịch bản từng service:**

| Service crash | Hệ thống phản ứng | Impact |
|--------------|------------------|--------|
| **Qdrant** | Circuit breaker mở → `/api/v1/chat` vẫn hoạt động (không có RAG context) | Mất semantic search, chat vẫn chạy |
| **Kafka** | Ingest scripts báo lỗi → data pipeline tạm dừng | Pipeline dừng, API Gateway không bị ảnh hưởng |
| **Redis (Feast)** | Feature store unavailable → scripts báo lỗi | Pipeline dừng, chat vẫn chạy |
| **FPT Cloud AI** | Circuit breaker → fallback response `[Demo mode]` | Mất LLM inference, API không crash |
| **Prometheus** | Mất metrics collection → không ảnh hưởng API Gateway | Mất observability tạm thời |

**Nguyên lý chung**: Mỗi external dependency đều có circuit breaker riêng. Khi một service crash, các service khác tiếp tục hoạt động với chức năng giới hạn (graceful degradation) thay vì cascade failure.
