import asyncio
import json
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from kafka import KafkaConsumer
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(tags=["WebSockets"])

KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'telemetry.live')

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Background task to read from Kafka and broadcast to WebSockets
async def kafka_to_websocket():
    while True:
        try:
            # Use a non-blocking or asyncio compatible Kafka consumer in production.
            # For simplicity, we use the standard KafkaConsumer in a thread or with small timeouts
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=[KAFKA_BROKER],
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='websocket-broadcaster',
                consumer_timeout_ms=1000 # Unblock periodically
            )
            print("WebSocket Broadcaster connected to Kafka.")
            
            while True:
                # We must await sleep to yield control back to the event loop
                await asyncio.sleep(0.1)
                
                # Poll kafka
                records = consumer.poll(timeout_ms=100)
                for topic_partition, messages in records.items():
                    for message in messages:
                        # Broadcast to all connected clients
                        payload = message.value.decode('utf-8')
                        await manager.broadcast(payload)
                        
        except Exception as e:
            print(f"WebSocket Kafka Consumer Error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
        finally:
            if 'consumer' in locals() and consumer:
                consumer.close()

@router.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, wait for client messages if any
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
