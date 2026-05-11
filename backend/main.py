import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kafka_fix

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from backend.routers import telemetry, websockets, ai
from backend.database.db import engine, Base

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Autonomous Fleet Reliability Platform",
    description="Backend API for Telemetry, RCA, and AI Copilot",
    version="2.0.0"
)

# Allow CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(telemetry.router)
app.include_router(websockets.router)
app.include_router(ai.router)

@app.on_event("startup")
async def startup_event():
    # Start the background task to bridge Kafka and WebSockets
    asyncio.create_task(websockets.kafka_to_websocket())

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Autonomous Fleet API is running."}
