#!/usr/bin/env python3
"""
FastAPI Backend for Traffic Management System
"""

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
from typing import Dict, List

app = FastAPI(title="Traffic Management API", version="1.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active connections
active_connections: List[WebSocket] = []

class SignalCommand(BaseModel):
    action: int  # 0: keep, 1: switch
    duration: int = None

@app.get("/")
async def root():
    return {"message": "Traffic Management System API", "status": "running"}

@app.get("/metrics")
async def get_metrics():
    """Get current traffic metrics"""
    # This would connect to your running simulation
    return {
        "waiting_times": {"N": 10, "S": 15, "E": 5, "W": 8},
        "queue_lengths": {"N": 3, "S": 4, "E": 2, "W": 2},
        "green_phase": "NS",
        "timestamp": "2024-01-01T00:00:00"
    }

@app.post("/control")
async def control_signal(command: SignalCommand):
    """Send control command to traffic light"""
    print(f"Received command: {command}")
    return {"status": "executed", "command": command}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Send updates every second
            await asyncio.sleep(1)
            metrics = {
                "type": "metrics_update",
                "data": await get_metrics()
            }
            await websocket.send_json(metrics)
    except:
        active_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
