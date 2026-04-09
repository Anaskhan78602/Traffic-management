import os
import sys

def setup_traci():
    possible_paths = [
        r"C:\Program Files (x86)\Eclipse\Sumo",
        r"C:\Program Files\Eclipse\Sumo"
    ]

    for path in possible_paths:
        if os.path.exists(path):
            tools_path = os.path.join(path, "tools")

            if tools_path not in sys.path:
                sys.path.insert(0, tools_path)

            os.environ["SUMO_HOME"] = path

            print("SUMO found at:", path)
            return True

    print("SUMO not found. Set SUMO_HOME manually.")
    return False