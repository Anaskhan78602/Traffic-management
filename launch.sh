#!/bin/bash
# Traffic Simulation Launcher

echo "========================================="
echo "   Traffic Management System"

echo "========================================="

# Set environment variables
export SUMO_HOME="/usr/local/share/sumo"
export PATH="$SUMO_HOME/bin:$PATH"
export PYTHONPATH="$HOME/traffic_project:$PYTHONPATH"

# Change to project directory
cd ~/traffic_project

# Check if Python modules exist
if [ ! -f "simulator/core.py" ]; then
    echo "❌ Simulator module not found!"
    echo "Please run the setup commands first."
    exit 1
fi

# Run the simulation
echo "Starting simulation..."
python3 -c "
from simulator.core import run_simulation
run_simulation(duration=100)
"

echo ""
echo "✅ Simulation finished!"