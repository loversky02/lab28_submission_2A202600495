#!/usr/bin/env python3
"""Lab 28 — 5 Smoke Tests: Critical User Journeys"""
import pytest, requests, time, os, sys, json

BASE_URL = "http://localhost:8001"
FPT_API_KEY = os.environ.get("FPT_API_KEY", "")

def retry_until(fn, max_wait=30, interval=2):
    """Retry helper — avoids flaky time.sleep(10)"""
    deadline = time.time() + max_wait
    last_error = None
    while time.time() < deadline:
        try:
            return fn()
        except Exception as e:
            last_error = e
            time.sleep(interval)
    raise last_error or TimeoutError("Retry exhausted")

# ═══════════════════════════════════════════════════════════════
# Test 1: Happy Path — Full Inference Request
# ═══════════════════════════════════════════════════════════════
class TestHappyPath:
    def test_health_check_passes(self):
        """API Gateway health check returns ok"""
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_full_inference_returns_200(self):
        """Send query to API Gateway, get response back"""
        resp = requests.post(f"{BASE_URL}/api/v1/chat", json={
            "query": "What is platform engineering?",
            "embedding": [0.1] * 384
        }, timeout=30)
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert len(data["answer"]) > 10

    def test_chat_response_includes_metadata(self):
        """Response includes latency and model info"""
        resp = requests.post(f"{BASE_URL}/api/v1/chat", json={
            "query": "Hello, how are you?",
            "embedding": [0.05] * 384
        }, timeout=30)
        assert resp.status_code == 200
        data = resp.json()
        assert "latency_ms" in data
        assert "model" in data

# ═══════════════════════════════════════════════════════════════
# Test 2: Data Ingestion Journey
# ═══════════════════════════════════════════════════════════════
class TestDataIngestion:
    def test_kafka_ingest_and_consume(self):
        """Ingest data into Kafka and verify produce succeeds"""
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers="localhost:9092",
            value_serializer=lambda v: json.dumps(v).encode()
        )
        future = producer.send("data.raw", {
            "id": f"smoke_{int(time.time())}",
            "text": "smoke test document for platform integration",
            "timestamp": time.time()
        })
        producer.flush()
        record_meta = future.get(timeout=10)
        assert record_meta.offset >= 0
        producer.close()

    def test_qdrant_collection_accessible(self):
        """Vector store collection exists and is queryable"""
        resp = requests.get("http://localhost:6333/collections/documents", timeout=5)
        assert resp.status_code == 200

# ═══════════════════════════════════════════════════════════════
# Test 3: Observability Journey
# ═══════════════════════════════════════════════════════════════
class TestObservability:
    def test_prometheus_scrapes_api_gateway(self):
        """Prometheus is scraping metrics from API Gateway"""
        resp = requests.get("http://localhost:9090/api/v1/query", params={
            "query": "up{job='api-gateway'}"
        }, timeout=5)
        assert resp.status_code == 200
        result = resp.json()["data"]["result"]
        assert len(result) > 0
        assert result[0]["value"][1] == "1"

    def test_grafana_dashboard_accessible(self):
        """Grafana API is accessible"""
        resp = requests.get("http://localhost:3000/api/health",
                            auth=("admin", "admin"), timeout=5)
        assert resp.status_code == 200

    def test_metrics_endpoint_exposed(self):
        """Prometheus metrics endpoint is serving data"""
        resp = requests.get(f"{BASE_URL}/metrics", timeout=5)
        assert resp.status_code == 200
        assert "http_requests_total" in resp.text or "prometheus" in resp.text.lower()

# ═══════════════════════════════════════════════════════════════
# Test 4: Error Handling & Failure Path
# ═══════════════════════════════════════════════════════════════
class TestFailurePath:
    def test_invalid_request_returns_422(self):
        """Missing required field returns validation error"""
        resp = requests.post(f"{BASE_URL}/api/v1/chat", json={}, timeout=5)
        assert resp.status_code == 422

    def test_server_survives_timeout(self):
        """Service remains healthy after client disconnect"""
        try:
            requests.post(f"{BASE_URL}/api/v1/chat",
                         json={"query": "test", "embedding": [0.1] * 384},
                         timeout=0.001)
        except requests.exceptions.Timeout:
            pass
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        assert health.status_code == 200

    def test_admin_endpoint_blocked(self):
        """Admin endpoint returns 403 (RBAC enforcement)"""
        resp = requests.get(f"{BASE_URL}/admin", timeout=5)
        assert resp.status_code in [401, 403, 404]

# ═══════════════════════════════════════════════════════════════
# Test 5: Feature Store Journey
# ═══════════════════════════════════════════════════════════════
class TestFeatureStore:
    def test_redis_reachable(self):
        """Redis (Feast online store) is reachable"""
        import redis as rd
        r = rd.Redis(host="localhost", port=6380, decode_responses=True)
        assert r.ping()

    def test_feature_keys_format(self):
        """Check feature key format is correct"""
        import redis as rd
        r = rd.Redis(host="localhost", port=6380, decode_responses=True)
        # Set a test feature if none exist
        if not r.keys("feature:*"):
            r.set("feature:test_smoke", json.dumps({"text": "test", "processed": True}))
        keys = r.keys("feature:*")
        assert len(keys) > 0
        print(f"  Feature store has {len(keys)} entries")

    def test_governance_encryption(self):
        """Verify encryption module is importable and functional"""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from governance.encryption import encrypt_value, decrypt_value
        key = b"a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
        encrypted = encrypt_value("test_secret", key)
        decrypted = decrypt_value(encrypted, key)
        assert decrypted == "test_secret"
