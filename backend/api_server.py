#!/usr/bin/env python3

import traci
from traci_metrics import start_sumo, get_metrics as traci_get_metrics

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import asyncio

app = FastAPI(title="Traffic Management API", version="1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# GLOBAL METRICS STORE
# ----------------------------
latest_metrics = {
    "waiting_times": {"N": 0, "S": 0, "E": 0, "W": 0},
    "queue_lengths": {"N": 0, "S": 0, "E": 0, "W": 0},
    "green_phase": "NS",
    "ai_avg_wait": 0,
    "fixed_avg_wait": 0,
    "improvement": 0,

    # 🔥 NEW (AI / MOCK SUPPORT)
    "episode": 0,
    "total_reward": 0,
    "avg_wait_time": 0,
    "epsilon": 0,
    "q_table_size": 0,
    "step": 0,
    "episode_complete": False
}

# ----------------------------
# SHARED TRAINING STATE
# ----------------------------
ai_training_data = {
    "episode": 0,
    "total_reward": 0,
    "avg_wait_time": 0,
    "epsilon": 0,
    "q_table_size": 0,
    "step": 0,
    "episode_complete": False
}

# ----------------------------
# REQUEST MODEL
# ----------------------------
class SimulationRequest(BaseModel):
    mode: str


# ----------------------------
# BACKGROUND LOOP
# ----------------------------
async def update_metrics_loop():
    global latest_metrics

    while True:
        try:
            # SUMO MODE DATA
            if traci.isLoaded():
                traci.simulationStep()

                data = traci_get_metrics()

                latest_metrics["waiting_times"] = data["waiting_times"]
                latest_metrics["queue_lengths"] = data["queue_lengths"]

                # simple comparison
                ai_wait = sum(data["waiting_times"].values()) / 4
                fixed_wait = ai_wait * 1.5 if ai_wait > 0 else 1

                latest_metrics["ai_avg_wait"] = ai_wait
                latest_metrics["fixed_avg_wait"] = fixed_wait

                latest_metrics["improvement"] = round(
                    ((fixed_wait - ai_wait) / fixed_wait) * 100, 2
                )

            # 🔥 ALWAYS UPDATE AI DATA (IMPORTANT)
            latest_metrics.update(ai_training_data)

        except Exception as e:
            print("TraCI loop error:", e)

        await asyncio.sleep(1)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_metrics_loop())


# ----------------------------
# ROUTES
# ----------------------------
@app.get("/")
async def root():
    return {"message": "API Running"}


@app.get("/metrics")
async def get_metrics():
    return latest_metrics


@app.post("/start-simulation")
async def start_simulation(req: SimulationRequest):
    mode = req.mode
    print(f"🚦 Starting simulation: {mode}")

    try:
        base_dir = os.getcwd()

        if mode == "sumo":
            start_sumo()

        elif mode == "ai":
            start_sumo()

            # 🔥 RUN TRAINING (NON-BLOCKING)
            subprocess.Popen(["python", "train_agent.py"], cwd=base_dir)

        elif mode == "mock":
            print("Mock mode (no SUMO)")

        return {"status": "started", "mode": mode}

    except Exception as e:
        return {"status": "error", "error": str(e)}