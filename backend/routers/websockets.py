import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from kafka import KafkaConsumer
from dotenv import load_dotenv
from pydantic import ValidationError

from backend.schemas.telemetry import VehicleTelemetry

load_dotenv()

router = APIRouter(tags=["WebSockets"])

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "telemetry.live")
USE_KAFKA_BRIDGE = os.getenv("TELEMETRY_USE_KAFKA", "false").lower() == "true"

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="kafka-ws")


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                pass


manager = ConnectionManager()


def validate_and_serialize(raw: dict | str) -> str | None:
    """Validate telemetry via Pydantic; return JSON string or None if rejected."""
    try:
        if isinstance(raw, str):
            data = json.loads(raw)
        else:
            data = raw
        point = VehicleTelemetry.from_raw(data)
        return point.to_json()
    except (ValidationError, json.JSONDecodeError, ValueError) as exc:
        print(f"Telemetry validation rejected: {exc}")
        return None


async def publish_telemetry(point: VehicleTelemetry) -> None:
    """Validated publish path used by the in-process generator."""
    payload = validate_and_serialize(point.model_dump(mode="json"))
    if payload:
        await manager.broadcast(payload)


def _create_consumer():
    return KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="websocket-broadcaster",
        consumer_timeout_ms=1000,
    )


def _poll_records(consumer):
    return consumer.poll(timeout_ms=500)


async def kafka_to_websocket():
    """Optional Kafka bridge — validates before broadcast."""
    loop = asyncio.get_running_loop()
    while True:
        consumer = None
        try:
            consumer = await loop.run_in_executor(_executor, _create_consumer)
            print("WebSocket Broadcaster connected to Kafka.")

            while True:
                records = await loop.run_in_executor(_executor, _poll_records, consumer)
                for _topic_partition, messages in records.items():
                    for message in messages:
                        payload = validate_and_serialize(message.value.decode("utf-8"))
                        if payload:
                            await manager.broadcast(payload)
                await asyncio.sleep(0.05)

        except Exception as e:
            print(f"WebSocket Kafka Consumer Error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
        finally:
            if consumer is not None:
                try:
                    await loop.run_in_executor(_executor, consumer.close)
                except Exception:
                    pass


@router.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
