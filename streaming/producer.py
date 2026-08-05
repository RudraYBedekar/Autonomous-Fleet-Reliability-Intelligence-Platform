"""
Kafka producer CLI — thin wrapper around backend.services.generator.

Publishes validated ground-vehicle telemetry to Kafka for the DB consumer.
The FastAPI backend runs the generator in-process by default (no Kafka needed).
"""

import json
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kafka_fix  # noqa: F401

from dotenv import load_dotenv
from kafka import KafkaProducer

from backend.services.generator import get_generator, TICK_INTERVAL_S

load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "telemetry.live")


def _serializer(data: dict) -> bytes:
    return json.dumps(data, default=str).encode("utf-8")


def get_producer() -> KafkaProducer | None:
    print(f"Connecting to Kafka broker at {KAFKA_BROKER}...")
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=_serializer,
            retries=5,
        )
        print("Successfully connected to Kafka.")
        return producer
    except Exception as e:
        print(f"Failed to connect to Kafka: {e}")
        return None


def run():
    producer = get_producer()
    generator = get_generator()
    print("Starting ground-vehicle telemetry producer (15 cars, 0–50 km/h)...")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            for point in generator.tick():
                payload = point.model_dump(mode="json")
                if producer:
                    producer.send(
                        KAFKA_TOPIC,
                        key=point.vehicle_id.encode("utf-8"),
                        value=payload,
                    )
                else:
                    print(payload)
            if producer:
                producer.flush()
            time.sleep(TICK_INTERVAL_S)
    except KeyboardInterrupt:
        print("\nProducer stopped.")
    finally:
        if producer:
            producer.close()


if __name__ == "__main__":
    run()
