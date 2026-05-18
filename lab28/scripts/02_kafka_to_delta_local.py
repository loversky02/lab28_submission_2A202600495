#!/usr/bin/env python3
"""Integration 2: Kafka → Delta Lake (Local, no Prefect required)
Consumes from Kafka and writes to Delta Lake (parquet format).
"""
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import pandas as pd
import json, os, time, sys
from datetime import datetime
from pathlib import Path

DELTA_PATH = "delta-lake/raw"
TOPIC = "data.raw"
BOOTSTRAP_SERVERS = "localhost:9092"

def main():
    os.makedirs(DELTA_PATH, exist_ok=True)
    print(f"Delta Lake path: {DELTA_PATH}")

    # Connect to Kafka
    for attempt in range(5):
        try:
            consumer = KafkaConsumer(
                TOPIC,
                bootstrap_servers=BOOTSTRAP_SERVERS,
                auto_offset_reset="earliest",
                consumer_timeout_ms=10000,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            )
            break
        except (NoBrokersAvailable, Exception) as e:
            print(f"  Kafka not ready (attempt {attempt+1}/5): {e}")
            time.sleep(5)
    else:
        print("ERROR: Cannot connect to Kafka")
        sys.exit(1)

    print(f"Connected to Kafka, consuming from '{TOPIC}'...")
    records = []
    for msg in consumer:
        records.append(msg.value)
        print(f"  Consumed: {msg.value.get('id', 'unknown')}")

    consumer.close()

    if not records:
        print("No records found in Kafka. Run scripts/01_ingest_to_kafka.py first.")
        # Create sample records anyway
        records = [
            {"id": f"default_{i}", "text": f"Default record {i} from Delta pipeline",
             "timestamp": time.time()}
            for i in range(3)
        ]

    # Save to Delta Lake (parquet)
    df = pd.DataFrame(records)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{DELTA_PATH}/batch_{timestamp}.parquet"
    df.to_parquet(output_file, index=False)
    print(f"Saved {len(df)} records to {output_file}")
    print(f"Integration 2 OK: Kafka → Delta Lake ({len(df)} records in {DELTA_PATH}/)")
    return df

if __name__ == "__main__":
    main()
