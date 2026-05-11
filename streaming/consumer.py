import json
import os
import sys
import datetime
import dateutil.parser

# Add parent dir to path so we can import backend and ml modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kafka_fix
from kafka import KafkaConsumer
from dotenv import load_dotenv

from backend.database.db import SessionLocal, engine, Base
from backend.database.models import TelemetryRecord
from ml.anomaly_detector import detect_anomaly_zscore, predict_rul_heuristic

load_dotenv()

KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'telemetry.live')

# Initialize DB tables
print("Initializing database tables...")
Base.metadata.create_all(bind=engine)

def get_consumer():
    print(f"Connecting to Kafka broker at {KAFKA_BROKER}...")
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='telemetry-db-writer',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        print("Successfully connected to Kafka.")
        return consumer
    except Exception as e:
        print(f"Failed to connect to Kafka: {e}")
        return None

def start_consuming():
    consumer = get_consumer()
    if not consumer:
        print("Exiting consumer due to connection failure.")
        return

    print(f"Listening to topic '{KAFKA_TOPIC}'...")
    db = SessionLocal()
    
    batch = []
    BATCH_SIZE = 50 # Write to DB in batches for performance
    
    try:
        for message in consumer:
            data = message.value
            
            # Parse timestamp
            try:
                ts = dateutil.parser.isoparse(data['timestamp'])
            except:
                ts = datetime.datetime.utcnow()
                
            # ML & Analytics Enrichment
            temp = data.get('temperature_c', 0)
            volt = data.get('voltage_v', 0)
            vib = data.get('vibration_g', 0)
            sensor = data.get('sensor_id', 'Unknown')
            
            # On-the-fly anomaly detection
            is_anomaly = detect_anomaly_zscore(temp, volt, vib)
            rul = predict_rul_heuristic(sensor, temp, volt, vib)
            
            record = TelemetryRecord(
                timestamp=ts,
                vehicle_id=data.get('vehicle_id'),
                sensor_id=sensor,
                temperature_c=temp,
                voltage_v=volt,
                vibration_g=vib,
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                status="Critical" if is_anomaly else data.get('status', 'Operational'),
                ml_anomaly=is_anomaly,
                predicted_rul_hours=rul
            )
            
            batch.append(record)
            
            if len(batch) >= BATCH_SIZE:
                db.bulk_save_objects(batch)
                db.commit()
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Saved batch of {len(batch)} records to DB.")
                batch = []
                
    except KeyboardInterrupt:
        print("\nConsumer Stopped.")
    finally:
        if batch:
            db.bulk_save_objects(batch)
            db.commit()
        db.close()
        consumer.close()

if __name__ == "__main__":
    start_consuming()
