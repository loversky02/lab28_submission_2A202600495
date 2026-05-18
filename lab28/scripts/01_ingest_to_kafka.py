#!/usr/bin/env python3
"""Ingest demo data into Kafka topic data.raw."""

import sys
import json
import time
import os
from kafka import KafkaProducer

KAFKA_SERVER = os.environ.get("KAFKA_SERVER", "localhost:9092")
DATA_PATH = sys.argv[1] if len(sys.argv) > 1 else "outputs/demo_dataset.json"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)


def load_data(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def ingest_data(records: list[dict]):
    for record in records:
        record["_ingest_ts"] = time.time()
        producer.send("data.raw", value=record)
        print(f"Sent: {record.get('id', record.get('text', '')[:40])}")
    producer.flush()
    print(f"Done: {len(records)} records ingested into Kafka topic 'data.raw'")


if __name__ == "__main__":
    if not os.path.exists(DATA_PATH):
        print(f"Data file not found: {DATA_PATH}")
        sys.exit(1)
    records = load_data(DATA_PATH)
    ingest_data(records)
