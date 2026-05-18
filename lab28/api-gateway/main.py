"""
Lab 28 — AI Platform API Gateway
Integrates: FPT Cloud AI (LLM + Embeddings) + Qdrant + Redis + Prometheus
5 layers: Compute → Data → ML → Ops → Governance
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from pydantic import BaseModel, Field
import httpx
import os
import time
import re
from typing import Optional

# ── Optional LangSmith ──────────────────────────────────────────
LANGCHAIN_API_KEY = os.environ.get("LANGCHAIN_API_KEY", "")
if LANGCHAIN_API_KEY:
    try:
        from langsmith import Client
        ls_client = Client(api_key=LANGCHAIN_API_KEY)
        print("LangSmith tracing enabled")
    except Exception:
        ls_client = None
else:
    ls_client = None

# ── App setup ──────────────────────────────────────────────────
app = FastAPI(
    title="AI Platform API Gateway",
    description="Lab 28 — Full 5-Layer AI Infrastructure Platform",
    version="1.0.0"
)

# Prometheus metrics (Integration 9)
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
)
instrumentator.instrument(app).expose(app)

# ── Config from environment ────────────────────────────────────
FPT_API_KEY = os.environ.get("FPT_API_KEY", "")
FPT_LLM_ENDPOINT = os.environ.get("FPT_LLM_ENDPOINT", "https://mkp-api.fptcloud.com/chat/completions")
FPT_EMBED_ENDPOINT = os.environ.get("FPT_EMBED_ENDPOINT", "https://mkp-api.fptcloud.com/embeddings")
FPT_LLM_MODEL = os.environ.get("FPT_LLM_MODEL", "Qwen2.5-7B-Instruct")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")

# ── Governance: Simple RBAC ────────────────────────────────────
API_KEYS = {
    "admin-key": {"role": "admin", "rate_limit": 100},
    "user-key": {"role": "user", "rate_limit": 20},
}

RBAC_PERMISSIONS = {
    "admin": ["chat", "search", "ingest", "admin", "metrics"],
    "user": ["chat", "search"],
}

_usage: dict[str, list[float]] = {}

# ── Governance: PII patterns ───────────────────────────────────
PII_PATTERNS = [
    r"\b\d{10,12}\b",
    r"\b\d{9,12}\b",
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
]

def mask_pii(text: str) -> str:
    for pattern in PII_PATTERNS:
        text = re.sub(pattern, "***REDACTED***", text, flags=re.IGNORECASE)
    return text

# ── Governance: RBAC check ─────────────────────────────────────
def check_rbac(api_key: Optional[str], action: str) -> bool:
    if api_key is None:
        return True
    if api_key not in API_KEYS:
        return False
    role = API_KEYS[api_key]["role"]
    return action in RBAC_PERMISSIONS.get(role, [])

def check_rate_limit(api_key: str) -> bool:
    if api_key not in API_KEYS:
        return False
    now = time.time()
    limit = API_KEYS[api_key]["rate_limit"]
    if api_key not in _usage:
        _usage[api_key] = []
    _usage[api_key] = [t for t in _usage[api_key] if now - t < 60]
    if len(_usage[api_key]) >= limit:
        return False
    _usage[api_key].append(now)
    return True

# ── Circuit breaker (simple) ──────────────────────────────────
_circuit_state: dict[str, dict] = {
    "llm": {"failures": 0, "last_failure": 0, "open": False},
    "embed": {"failures": 0, "last_failure": 0, "open": False},
    "qdrant": {"failures": 0, "last_failure": 0, "open": False},
}
CIRCUIT_THRESHOLD = 3
CIRCUIT_TIMEOUT_SEC = 30

def circuit_breaker(service: str) -> bool:
    s = _circuit_state.get(service, {})
    if not s.get("open", False):
        return True
    if time.time() - s.get("last_failure", 0) > CIRCUIT_TIMEOUT_SEC:
        s["open"] = False
        s["failures"] = 0
        return True
    return False

def record_failure(service: str):
    s = _circuit_state.get(service, {})
    s["failures"] = s.get("failures", 0) + 1
    s["last_failure"] = time.time()
    if s["failures"] >= CIRCUIT_THRESHOLD:
        s["open"] = True

def record_success(service: str):
    if service in _circuit_state:
        _circuit_state[service]["failures"] = 0
        _circuit_state[service]["open"] = False

# ── Pydantic models ────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    embedding: Optional[list[float]] = Field(default=None)
    api_key: Optional[str] = Field(default=None)

class ChatResponse(BaseModel):
    answer: str
    latency_ms: float
    model: str
    context_used: bool = False

class IngestRequest(BaseModel):
    texts: list[str] = Field(..., min_items=1, max_items=100)

class HealthResponse(BaseModel):
    status: str
    layers: dict

# ── Health check ───────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse)
async def health():
    return {
        "status": "ok",
        "layers": {
            "layer1_compute": "FPT Cloud AI (Qwen2.5-7B + Vietnamese Embedding)",
            "layer2_data": "Kafka:9092 + Qdrant:6333",
            "layer3_ml": "Prefect:4200 + Feast/Redis:6379",
            "layer4_ops": "Prometheus:9090 + Grafana:3000",
            "layer5_governance": "RBAC + PII masking + circuit breaker",
        }
    }

# ── Admin endpoint (returns 403) ───────────────────────────────
@app.get("/admin")
async def admin():
    raise HTTPException(status_code=403, detail="Admin access requires authentication")

# ── Metrics summary ────────────────────────────────────────────
@app.get("/metrics-summary")
async def metrics_summary():
    return {
        "circuit_breakers": _circuit_state,
        "active_rate_limiters": {k: len(v) for k, v in _usage.items()},
    }

# ── Chat endpoint ──────────────────────────────────────────────
@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start = time.time()
    query = mask_pii(request.query)  # Layer 5: PII masking

    # RBAC
    if request.api_key:
        if not check_rbac(request.api_key, "chat"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        if not check_rate_limit(request.api_key):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

    context_used = False
    context_text = ""

    # Vector search (optional — graceful degradation)
    if circuit_breaker("qdrant"):
        try:
            vector = request.embedding or [0.0] * 384
            async with httpx.AsyncClient() as client:
                search_resp = await client.post(
                    f"{QDRANT_URL}/collections/documents/points/search",
                    json={"vector": vector, "limit": 3},
                    timeout=5.0
                )
            if search_resp.status_code == 200:
                results = search_resp.json().get("result", [])
                if results:
                    context_text = " ".join(
                        r.get("payload", {}).get("text", "") for r in results
                    )
                    context_used = True
            record_success("qdrant")
        except Exception:
            record_failure("qdrant")

    # LLM via FPT Cloud AI
    if not circuit_breaker("llm"):
        raise HTTPException(status_code=503, detail="LLM service temporarily unavailable")

    if not FPT_API_KEY:
        return ChatResponse(
            answer=f"[Demo mode] You asked: {query}. "
                   f"Set FPT_API_KEY in .env for live AI inference.",
            latency_ms=round((time.time() - start) * 1000, 2),
            model="fallback/demo",
            context_used=context_used,
        )

    system_prompt = "You are a helpful AI assistant. Answer concisely."
    if context_text:
        system_prompt += f"\n\nContext:\n{context_text}"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            llm_resp = await client.post(
                FPT_LLM_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {FPT_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": FPT_LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query},
                    ],
                    "stream": False,
                },
            )
        if llm_resp.status_code != 200:
            record_failure("llm")
            raise HTTPException(status_code=502, detail=f"LLM error: {llm_resp.status_code}")

        result = llm_resp.json()
        answer = result["choices"][0]["message"]["content"]
        model_used = result.get("model", FPT_LLM_MODEL)
        record_success("llm")

        # LangSmith trace
        if ls_client:
            try:
                ls_client.create_run(
                    name="chat-request",
                    run_type="chain",
                    inputs={"query": query, "context": context_text[:200]},
                    outputs={"answer": answer[:200]},
                    project_name=os.environ.get("LANGCHAIN_PROJECT", "lab28-platform"),
                )
            except Exception:
                pass

        return ChatResponse(
            answer=answer,
            latency_ms=round((time.time() - start) * 1000, 2),
            model=model_used,
            context_used=context_used,
        )

    except httpx.TimeoutException:
        record_failure("llm")
        raise HTTPException(status_code=504, detail="LLM timeout")

# ── Search endpoint ────────────────────────────────────────────
@app.post("/api/v1/search")
async def search(request: ChatRequest):
    if not circuit_breaker("qdrant"):
        raise HTTPException(status_code=503, detail="Vector search unavailable")

    vector = request.embedding or [0.0] * 384
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{QDRANT_URL}/collections/documents/points/search",
                json={"vector": vector, "limit": 5},
                timeout=5.0
            )
        return resp.json()
    except Exception as e:
        return JSONResponse(status_code=503, content={"error": str(e)})

# ── Embedding endpoint ─────────────────────────────────────────
@app.post("/api/v1/embed")
async def embed(request: IngestRequest):
    if not FPT_API_KEY:
        raise HTTPException(status_code=501, detail="Requires FPT_API_KEY")

    if not circuit_breaker("embed"):
        raise HTTPException(status_code=503, detail="Embedding service unavailable")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                FPT_EMBED_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {FPT_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "input": request.texts,
                    "model": os.environ.get("FPT_EMBED_MODEL", "Vietnamese_Embedding"),
                },
            )
        if resp.status_code != 200:
            record_failure("embed")
            raise HTTPException(status_code=502, detail=f"Embedding error: {resp.status_code}")
        data = resp.json()
        record_success("embed")
        return {"embeddings": [d["embedding"] for d in data.get("data", [])]}
    except Exception as e:
        record_failure("embed")
        raise HTTPException(status_code=502, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print(f"FPT LLM:    {FPT_LLM_ENDPOINT} ({FPT_LLM_MODEL})")
    print(f"FPT Embed:  {FPT_EMBED_ENDPOINT}")
    print(f"API Key:    {'configured' if FPT_API_KEY else 'MISSING'}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
