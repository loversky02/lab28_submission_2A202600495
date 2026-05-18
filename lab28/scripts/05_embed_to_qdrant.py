#!/usr/bin/env python3
"""Embed documents via FPT Cloud AI and store in Qdrant vector store."""

import os
import sys
import json
import time
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

FPT_API_KEY = os.environ.get("FPT_API_KEY", "")
FPT_EMBED_ENDPOINT = os.environ.get("FPT_EMBED_ENDPOINT", "https://mkp-api.fptcloud.com/embeddings")
FPT_EMBED_MODEL = os.environ.get("FPT_EMBED_MODEL", "Vietnamese_Embedding")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")

qdrant = QdrantClient(url=QDRANT_URL)

# FPT embeddings return 768-dim vectors for Vietnamese_Embedding
# default to 768; multilingual-e5-large also returns 1024
EMBED_DIM = int(os.environ.get("EMBED_DIM", "768"))


def create_collection(collection_name: str = "documents") -> None:
    try:
        qdrant.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
        )
        print(f"[qdrant] Collection '{collection_name}' created (dim={EMBED_DIM})")
    except Exception as e:
        print(f"[qdrant] Collection may already exist: {e}")


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Call FPT Cloud AI embeddings API."""
    if not FPT_API_KEY:
        print("[embed] No FPT_API_KEY set — using mock zero vectors")
        return [[0.0] * EMBED_DIM for _ in texts]

    headers = {
        "Authorization": f"Bearer {FPT_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "input": texts,
        "model": FPT_EMBED_MODEL,
    }

    resp = requests.post(FPT_EMBED_ENDPOINT, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        print(f"[embed] FPT API error {resp.status_code}: {resp.text[:200]}")
        return [[0.0] * EMBED_DIM for _ in texts]

    data = resp.json()
    # OpenAI-compatible: {"data": [{"embedding": [...]}, ...]}
    embeddings = [item["embedding"] for item in data.get("data", [])]
    actual_dim = len(embeddings[0]) if embeddings else EMBED_DIM
    print(f"[embed] Got {len(embeddings)} vectors, dim={actual_dim}")
    return embeddings


def embed_and_store(records: list[dict], collection_name: str = "documents") -> int:
    texts = [r.get("text", r.get("content", "")) for r in records]
    embeddings = get_embeddings(texts)

    points = [
        PointStruct(id=i, vector=emb, payload=rec)
        for i, (emb, rec) in enumerate(zip(embeddings, records))
    ]
    qdrant.upsert(collection_name=collection_name, points=points)
    print(f"[qdrant] {len(points)} vectors stored in '{collection_name}'")
    return len(points)


def load_records(path: str = "outputs/demo_data.json") -> list[dict]:
    if not os.path.exists(path):
        print(f"[embed] No data file at {path}, using sample data")
        return [
            {"id": "doc_001", "text": "AI platform integration test"},
            {"id": "doc_002", "text": "Kafka to Delta Lake pipeline"},
        ]
    with open(path) as f:
        return json.load(f)


if __name__ == "__main__":
    collection = sys.argv[1] if len(sys.argv) > 1 else "documents"
    data_path = sys.argv[2] if len(sys.argv) > 2 else "outputs/demo_data.json"

    create_collection(collection)
    records = load_records(data_path)
    count = embed_and_store(records, collection)
    print(f"\nDone: {count} records embedded and stored in Qdrant.")
