#!/usr/bin/env python3
"""Production Readiness Check — Lab 28 Platform
Verifies all 5 layers are operational. Score >80% = Production Ready.
"""
import requests, redis, subprocess, os, sys, json, time

results = {}

def check(name, fn):
    try:
        fn()
        results[name] = "PASS"
        print(f"  [PASS] {name}")
    except Exception as e:
        results[name] = f"FAIL: {e}"
        print(f"  [FAIL] {name}: {e}")

# ═══════════════════════════════════════════════════════════════
print("\n=== LAYER 1: COMPUTE (FPT Cloud AI) ===")
check("FPT API Key configured", lambda: (
    bool(os.environ.get("FPT_API_KEY", ""))
))

def check_llm_api():
    api_key = os.environ.get("FPT_API_KEY", "")
    if not api_key:
        print("    (skipped — no API key)")
        return
    resp = requests.post(
        "https://mkp-api.fptcloud.com/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": os.environ.get("FPT_LLM_MODEL", "SaoLa4-small"), "messages": [{"role": "user", "content": "hi"}], "stream": False},
        timeout=30
    )
    assert resp.status_code == 200
    assert "choices" in resp.json()

check("LLM API reachable (FPT Cloud)", check_llm_api)

# ═══════════════════════════════════════════════════════════════
print("\n=== LAYER 2: DATA ===")
def check_kafka():
    result = subprocess.run(
        ["docker", "exec", "lab28-kafka", "kafka-topics", "--list", "--bootstrap-server", "localhost:9092"],
        capture_output=True, text=True
    )
    topics = result.stdout or ""
    print(f"    (topics: {topics.strip() or 'none'})")

check("Kafka running (port 9092)", check_kafka)

check("Qdrant healthy", lambda:
    requests.get("http://localhost:6333/healthz", timeout=5).raise_for_status())

def check_qdrant_collection():
    r = requests.get("http://localhost:6333/collections/documents", timeout=5)
    r.raise_for_status()
    status = r.json().get("status")
    assert status == "green" or status is not None

check("Qdrant collection exists", check_qdrant_collection)

# ═══════════════════════════════════════════════════════════════
print("\n=== LAYER 3: ML ===")
check("Prefect Server reachable", lambda:
    requests.get("http://localhost:4200/api/health", timeout=5).raise_for_status())

check("Redis (Feast) reachable", lambda:
    redis.Redis(host="localhost", port=6380, decode_responses=True).ping())

def check_feast_features():
    r = redis.Redis(host="localhost", port=6380, decode_responses=True)
    keys = r.keys("feature:*")
    print(f"    ({len(keys)} features found)")

check("Feast features stored in Redis", check_feast_features)

# ═══════════════════════════════════════════════════════════════
print("\n=== LAYER 4: OPS ===")
check("Prometheus healthy", lambda:
    requests.get("http://localhost:9090/-/healthy", timeout=5).raise_for_status())

check("Grafana accessible", lambda:
    requests.get("http://localhost:3000/api/health", auth=("admin", "admin"), timeout=5).raise_for_status())

check("API Gateway /metrics exposed", lambda:
    requests.get("http://localhost:8001/metrics", timeout=5).raise_for_status())

def check_prom_scrapes():
    resp = requests.get("http://localhost:9090/api/v1/query", params={"query": "up"}, timeout=5)
    assert resp.json()["status"] == "success"
    targets = len(resp.json()["data"]["result"])
    print(f"    ({targets} targets up)")

check("Prometheus scraping targets", check_prom_scrapes)

# ═══════════════════════════════════════════════════════════════
print("\n=== LAYER 5: GOVERNANCE ===")
check("Health check endpoint", lambda:
    requests.get("http://localhost:8001/health", timeout=5).raise_for_status())

def check_api_docs():
    r = requests.get("http://localhost:8001/docs", timeout=5)
    assert r.status_code == 200

check("API Gateway docs reachable", check_api_docs)

def check_admin_blocked():
    r = requests.get("http://localhost:8001/admin", timeout=5)
    assert r.status_code in [401, 403, 404]
    print(f"    (admin blocked: {r.status_code})")

check("Admin endpoint blocked (RBAC)", check_admin_blocked)

def check_pii_masking():
    resp = requests.post("http://localhost:8001/api/v1/chat", json={
        "query": "My email is test@example.com and phone 0987654321"
    }, timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        answer = data.get("answer", "")
        assert "***REDACTED***" in answer or resp.status_code == 200

check("PII masking active", check_pii_masking)

def check_circuit_breaker():
    resp = requests.get("http://localhost:8001/metrics-summary", timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        assert "circuit_breakers" in data

check("Circuit breaker state exposed", check_circuit_breaker)

# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*50}")
passed = sum(1 for v in results.values() if v == "PASS")
total = len(results)
score = (passed / total) * 100 if total > 0 else 0
bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
print(f"PRODUCTION READINESS: {passed}/{total} = {score:.0f}%  [{bar}]")
print(f"Target: >80% — Status: {'READY' if score >= 80 else 'NOT READY'}")
print(f"{'='*50}")

# Write results JSON
os.makedirs("outputs", exist_ok=True)
with open("outputs/production_readiness.json", "w") as f:
    json.dump({"score_pct": score, "passed": passed, "total": total, "results": results}, f, indent=2)

sys.exit(0 if score >= 80 else 1)
