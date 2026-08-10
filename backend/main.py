import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kafka_fix  # noqa: F401 — Python 3.12 Kafka selector patch

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from backend.routers import telemetry, websockets, ai, fleet, datahub, fleetguard
from backend.database.db import engine, Base
from backend.services.generator import get_generator
import backend.services.generator as generator_module
import backend.services.fleet_manifest as fleet_manifest_module

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Autonomous Fleet Reliability Platform",
    description="Backend API for Telemetry, RCA, and AI Copilot",
    version="2.1.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry.router)
app.include_router(websockets.router)
app.include_router(ai.router)
app.include_router(fleet.router)
app.include_router(datahub.router)
app.include_router(fleetguard.router)



from backend.datahub.live_publisher import publish_live_fleet_metadata


@app.on_event("startup")
async def startup_event():
    # Publish live application telemetry dataset, schema, and ML lineage to DataHub GMS
    try:
        publish_live_fleet_metadata()
    except Exception as e:
        print(f"[DataHub] Live startup metadata publishing skipped: {e}")

    use_kafka = os.getenv("TELEMETRY_USE_KAFKA", "false").lower() == "true"

    if use_kafka:
        asyncio.create_task(websockets.kafka_to_websocket())
    else:
        generator_module._generator = None
        fleet_manifest_module._manifests = None
        generator = get_generator()

        async def run_generator():
            await generator.run(websockets.publish_telemetry)

        asyncio.create_task(run_generator())



@app.get("/")
def read_root():
    return {
        "status": "ok",
        "message": "Autonomous Fleet API is running.",
        "fleet_size": 15,
        "vehicle_ids": [f"car-{i:03d}" for i in range(1, 16)],
    }
