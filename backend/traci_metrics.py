import traci
import threading
import os

latest_metrics = {}
simulation_running = False


def run_sumo():
    global latest_metrics, simulation_running

    # 🔥 SAFE RESTART
    try:
        if traci.isLoaded():
            print("♻️ Restarting SUMO...")
            traci.close()
    except:
        pass

    base_dir = os.path.dirname(os.path.abspath(__file__))
    sumo_cfg = os.path.join(base_dir, "simulator", "sumo_sim", "osm.sumocfg")

    if not os.path.exists(sumo_cfg):
        raise FileNotFoundError(f"SUMO config not found at: {sumo_cfg}")

    simulation_running = True

    traci.start([
        "sumo-gui",
        "-c", sumo_cfg
    ])

    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()

        edges = traci.edge.getIDList()

        queue_lengths = {"N": 0, "S": 0, "E": 0, "W": 0}
        waiting_times = {"N": 0, "S": 0, "E": 0, "W": 0}

        for edge in edges:
            vehicles = traci.edge.getLastStepVehicleIDs(edge)

            direction = None
            edge_lower = edge.lower()

            if "n" in edge_lower:
                direction = "N"
            elif "s" in edge_lower:
                direction = "S"
            elif "e" in edge_lower:
                direction = "E"
            elif "w" in edge_lower:
                direction = "W"

            if direction is None:
                continue

            queue_lengths[direction] += len(vehicles)

            total_waiting = 0
            for v in vehicles:
                total_waiting += traci.vehicle.getWaitingTime(v)

            waiting_times[direction] += total_waiting

        latest_metrics = {
            "queue_lengths": queue_lengths,
            "waiting_times": waiting_times
        }

    traci.close()
    simulation_running = False


def start_sumo():
    thread = threading.Thread(target=run_sumo, daemon=True)
    thread.start()


def get_metrics():
    return latest_metrics


def is_running():
    return simulation_running