import json
import os
import sys
import datetime
import time
import dateutil.parser

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kafka_fix  # noqa: F401
from kafka import KafkaConsumer
from dotenv import load_dotenv
from pydantic import ValidationError

from backend.database.db import SessionLocal, engine, Base
from backend.database.models import TelemetryRecord
from backend.schemas.telemetry import VehicleTelemetry

load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "telemetry.live")

print("Initializing database tables...")
Base.metadata.create_all(bind=engine)


def get_consumer():
    print(f"Connecting to Kafka broker at {KAFKA_BROKER}...")
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset="latest",
            enable_auto_commit=True,
            group_id="telemetry-db-writer",
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        )
        print("Successfully connected to Kafka.")
        return consumer
    except Exception as e:
        print(f"Failed to connect to Kafka: {e}")
        return None


def save_batch(db, batch):
    if not batch:
        return

    for attempt in range(5):
        try:
            db.bulk_save_objects(batch)
            db.commit()
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Saved batch of {len(batch)} records to DB.")
            return
        except Exception as e:
            db.rollback()
            if attempt == 4:
                raise
            print(f"DB write retry {attempt + 1}/5 after error: {e}")
            time.sleep(0.5 * (attempt + 1))


def to_record(data: dict) -> TelemetryRecord | None:
    try:
        point = VehicleTelemetry.from_raw(data)
    except ValidationError as exc:
        print(f"Skipping invalid telemetry: {exc}")
        return None

    return TelemetryRecord(
        timestamp=point.timestamp,
        vehicle_id=point.vehicle_id,
        sensor_id="ground",
        temperature_c=0.0,
        voltage_v=0.0,
        vibration_g=0.0,
        latitude=point.lat,
        longitude=point.lng,
        speed_kmh=point.speed_kmh,
        status=point.status,
        ml_anomaly=False,
        predicted_rul_hours=None,
    )


def start_consuming():
    consumer = get_consumer()
    if not consumer:
        print("Exiting consumer due to connection failure.")
        return

    print(f"Listening to topic '{KAFKA_TOPIC}'...")
    db = SessionLocal()
    batch = []
    BATCH_SIZE = 50

    try:
        for message in consumer:
            record = to_record(message.value)
            if record is None:
                continue
            batch.append(record)
            if len(batch) >= BATCH_SIZE:
                save_batch(db, batch)
                batch = []
    except KeyboardInterrupt:
        print("\nConsumer Stopped.")
    finally:
        try:
            save_batch(db, batch)
        except Exception as e:
            print(f"Failed to flush final batch: {e}")
        db.close()
        consumer.close()


if __name__ == "__main__":
    start_consuming()
