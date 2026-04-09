#!/usr/bin/env python3
"""
Traffic Simulator Core Module (Updated for RL Project)
Supports MOCK simulation + optional SUMO integration
"""

import random
import os
import sys

# ---------------- SUMO SETUP ----------------
SUMO_HOME = os.environ.get("SUMO_HOME", r"C:\Program Files (x86)\Eclipse\Sumo")

if os.path.exists(SUMO_HOME):
    tools = os.path.join(SUMO_HOME, "tools")
    if tools not in sys.path:
        sys.path.append(tools)
    print(f"✓ SUMO tools found at: {tools}")

try:
    import traci
    TRACI_AVAILABLE = True
    print("✓ TraCI module loaded")
except ImportError:
    TRACI_AVAILABLE = False
    print("⚠ TraCI not available - using mock simulator")


class TrafficSimulator:
    """Main traffic simulator class"""

    def __init__(self, use_mock=True):
        self.use_mock = use_mock or not TRACI_AVAILABLE

        self.time = 0
        self.step_count = 0
        self.sumo_connected = False

        if self.use_mock:
            self._init_mock()
        else:
            self._init_sumo()

    # ---------------- MOCK INIT ----------------
    def _init_mock(self):
        print("🚦 MOCK simulator running")

        self.queue_lengths = {'N': 0, 'S': 0, 'E': 0, 'W': 0}
        self.waiting_times = {'N': 0, 'S': 0, 'E': 0, 'W': 0}

        self.green_phase = 'NS'
        self.green_timer = 0
        self.min_green = 5

    # ---------------- SUMO INIT (SAFE) ----------------
    def _init_sumo(self):
        print("Initializing REAL SUMO simulator...")

        try:
            traci.start(["sumo", "-c", "test_simulation.sumocfg"])
            self.sumo_connected = True
            print("✓ SUMO connected")
        except Exception as e:
            print(f"⚠ SUMO failed: {e}")
            print("➡ Falling back to MOCK")
            self.use_mock = True
            self._init_mock()

    # ---------------- STATE ----------------
    def _get_state(self):
        state = []
        for d in ['N', 'S', 'E', 'W']:
            q = self.queue_lengths[d]
            if q < 3:
                state.append(0)
            elif q < 7:
                state.append(1)
            else:
                state.append(2)
        return tuple(state)

    # ---------------- MOCK STEP ----------------
    def _step_mock(self, action):

        # Switch signal
        if action == 1 and self.green_timer >= self.min_green:
            self.green_phase = 'EW' if self.green_phase == 'NS' else 'NS'
            self.green_timer = 0

        # Vehicle arrivals
        for d in self.queue_lengths:
            if random.random() < 0.3:
                self.queue_lengths[d] += random.randint(1, 2)

        # Movement
        active = ['N', 'S'] if self.green_phase == 'NS' else ['E', 'W']

        for d in active:
            passed = min(self.queue_lengths[d], 2)
            self.queue_lengths[d] -= passed

        # Waiting time update
        for d in self.queue_lengths:
            self.waiting_times[d] += self.queue_lengths[d] * 0.5

        # Timing update
        self.green_timer += 1
        self.time += 1
        self.step_count += 1

        # Reward (negative of congestion)
        total_queue = sum(self.queue_lengths.values())
        total_wait = sum(self.waiting_times.values())

        reward = -(total_queue * 2 + total_wait * 0.1)

        return self._get_state(), reward

    # ---------------- SUMO STEP ----------------
    def _step_sumo(self, action):
        try:
            traci.simulationStep()

            vehicles = traci.vehicle.getIDList()
            total_wait = sum(traci.vehicle.getWaitingTime(v) for v in vehicles)

            self.time += 1
            self.step_count += 1

            state = (0, 0, 0, 0)
            reward = -total_wait

            return state, reward

        except Exception as e:
            print(f"SUMO error: {e} → switching to MOCK")
            self.use_mock = True
            self._init_mock()
            return self._step_mock(action)

    # ---------------- PUBLIC STEP ----------------
    def step(self, action):
        if self.use_mock:
            return self._step_mock(action)
        else:
            return self._step_sumo(action)

    # ---------------- METRICS ----------------
    def get_metrics(self):
        return {
            "time": self.time,
            "step": self.step_count,
            "queue_lengths": self.queue_lengths.copy() if self.use_mock else {},
            "waiting_times": self.waiting_times.copy() if self.use_mock else {},
            "total_waiting_time": sum(self.waiting_times.values()) if self.use_mock else 0,
            "green_phase": self.green_phase if self.use_mock else None,
            "green_timer": self.green_timer if self.use_mock else None,
            "simulator_type": "mock" if self.use_mock else "sumo"
        }

    # ---------------- RESET ----------------
    def reset(self):
        self.time = 0
        self.step_count = 0

        if self.use_mock:
            self._init_mock()
        else:
            if self.sumo_connected:
                traci.close()
            self._init_sumo()

    # ---------------- CLOSE ----------------
    def close(self):
        if not self.use_mock and self.sumo_connected:
            traci.close()
            print("SUMO connection closed")


# ---------------- TEST RUN ----------------
def run_simulation(duration=100):
    print("\n=== RUNNING SIMULATION ===\n")

    sim = TrafficSimulator(use_mock=True)

    for step in range(duration):
        action = random.choice([0, 1])
        state, reward = sim.step(action)

        if step % 10 == 0:
            m = sim.get_metrics()
            print(f"Step {step} | Wait: {m['total_waiting_time']:.1f} | Phase: {m['green_phase']}")

    sim.close()


if __name__ == "__main__":
    run_simulation()