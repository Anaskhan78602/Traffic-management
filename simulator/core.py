#!/usr/bin/env python3
"""
Traffic Simulator Core Module
Supports both real SUMO and mock simulation
"""

import random
import os
import sys

# Try to load SUMO tools
SUMO_TOOLS_PATH = "/usr/local/share/sumo/tools"
if os.path.exists(SUMO_TOOLS_PATH):
    sys.path.insert(0, SUMO_TOOLS_PATH)
    print(f"✓ SUMO tools found at: {SUMO_TOOLS_PATH}")

# Try to import traci (don't call any functions yet)
try:
    import traci
    TRACI_AVAILABLE = True
    print("✓ TraCI module loaded")
except ImportError:
    TRACI_AVAILABLE = False
    print("⚠ TraCI not available - using mock simulator")
    print("  Install with: pip3 install traci")

class TrafficSimulator:
    """Main traffic simulator class"""
    
    def __init__(self, use_mock=False):
        """Initialize simulator"""
        self.use_mock = use_mock or not TRACI_AVAILABLE
        self.time = 0
        self.step_count = 0
        self.sumo_connected = False
        
        if self.use_mock:
            self._init_mock()
        else:
            self._init_sumo()
    
    def _init_mock(self):
        """Initialize mock simulation"""
        print("Initializing MOCK traffic simulator...")
        self.waiting_times = {'N': 0, 'S': 0, 'E': 0, 'W': 0}
        self.queue_lengths = {'N': 0, 'S': 0, 'E': 0, 'W': 0}
        self.vehicles_processed = {'N': 0, 'S': 0, 'E': 0, 'W': 0}
        self.green_phase = 'NS'  # 'NS' or 'EW'
        self.green_timer = 0
        self.min_green = 5
        print("✓ Mock simulator ready")
    
    def _init_sumo(self):
        """Initialize real SUMO simulation"""
        print("Initializing REAL SUMO simulator...")
        try:
            # Create a simple test configuration
            self._create_sumo_config()
            
            # Start SUMO
            sumo_binary = "sumo"  # Use "sumo-gui" for visualization
            self.sumo_cmd = [sumo_binary, "-c", "test_simulation.sumocfg", "--start"]
            traci.start(self.sumo_cmd)
            self.sumo_connected = True
            print(f"✓ SUMO started with PID")
            print(f"✓ TraCI connected")
        except Exception as e:
            print(f"⚠ Failed to start SUMO: {e}")
            print("  Falling back to mock simulator...")
            self.use_mock = True
            self._init_mock()
    
    def _create_sumo_config(self):
        """Create a simple SUMO configuration for testing"""
        # Create network file
        net_file = "test_network.net.xml"
        if not os.path.exists(net_file):
            with open(net_file, 'w') as f:
                f.write('''<?xml version="1.0" encoding="UTF-8"?>
<net version="1.3" junctionCornerDetail="5">
    <edge id="E1" from="J1" to="J2" priority="3" numLanes="2" speed="13.89"/>
    <edge id="E2" from="J2" to="J1" priority="3" numLanes="2" speed="13.89"/>
</net>''')
        
        # Create route file
        route_file = "test_routes.rou.xml"
        if not os.path.exists(route_file):
            with open(route_file, 'w') as f:
                f.write('''<?xml version="1.0" encoding="UTF-8"?>
<routes>
    <vType id="car" accel="2.6" decel="4.5" length="5" maxSpeed="13.89"/>
    <route id="route1" edges="E1 E2"/>
    <flow id="flow1" type="car" route="route1" begin="0" end="100" period="2"/>
</routes>''')
        
        # Create config file
        config_file = "test_simulation.sumocfg"
        with open(config_file, 'w') as f:
            f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <input>
        <net-file value="{net_file}"/>
        <route-files value="{route_file}"/>
    </input>
    <time>
        <begin value="0"/>
        <end value="3600"/>
        <step-length value="1.0"/>
    </time>
</configuration>''')
    
    def step(self, action):
        """Execute one simulation step with given action"""
        if self.use_mock:
            return self._step_mock(action)
        else:
            return self._step_sumo(action)
    
    def _step_mock(self, action):
        """Mock simulation step"""
        
        # Action: 0 = keep current phase, 1 = switch phase
        if action == 1 and self.green_timer >= self.min_green:
            self.green_phase = 'EW' if self.green_phase == 'NS' else 'NS'
            self.green_timer = 0
        
        # Generate random vehicle arrivals
        for direction in self.waiting_times:
            # Random arrival probability
            if random.random() < 0.3:  # 30% chance
                self.queue_lengths[direction] += 1
                self.waiting_times[direction] += random.uniform(0, 10)
        
        # Process vehicles based on green phase
        if self.green_phase == 'NS':
            moving_directions = ['N', 'S']
        else:
            moving_directions = ['E', 'W']
        
        for direction in moving_directions:
            # Vehicles that can pass (2 per step)
            vehicles_passing = min(self.queue_lengths[direction], 2)
            self.queue_lengths[direction] -= vehicles_passing
            self.vehicles_processed[direction] += vehicles_passing
            
            # Reduce waiting time for passing vehicles
            self.waiting_times[direction] = max(0, self.waiting_times[direction] - vehicles_passing * 5)
        
        # Increase waiting time for vehicles still in queue
        for direction in self.waiting_times:
            self.waiting_times[direction] += self.queue_lengths[direction] * 1.5
        
        # Update timers
        self.green_timer += 1
        self.time += 1
        self.step_count += 1
        
        # Calculate total waiting time (negative for reward)
        total_waiting_time = sum(self.waiting_times.values())
        reward = -total_waiting_time
        
        # Get current state
        state = self._get_state()
        
        return state, reward
    
    def _step_sumo(self, action):
        """Real SUMO simulation step"""
        if self.sumo_connected:
            try:
                traci.simulationStep()
                # Collect metrics from SUMO
                # This is where you'd get real traffic data
                
                # For now, just increment time
                self.time += 1
                self.step_count += 1
                
                # Mock reward for now
                state = (0, 0, 0, 0)
                reward = 0
                
                return state, reward
            except Exception as e:
                print(f"SUMO error: {e}, falling back to mock")
                self.use_mock = True
                return self._step_mock(action)
        else:
            return self._step_mock(action)
    
    def _get_state(self):
        """Get current state for Q-learning"""
        # Discretize queue lengths into bins
        state = []
        for direction in ['N', 'S', 'E', 'W']:
            q = self.queue_lengths[direction]
            if q < 3:
                state.append(0)  # Low
            elif q < 7:
                state.append(1)  # Medium
            else:
                state.append(2)  # High
        return tuple(state)
    
    def get_metrics(self):
        """Get current simulation metrics"""
        if self.use_mock:
            return {
                'time': self.time,
                'step': self.step_count,
                'total_waiting_time': sum(self.waiting_times.values()),
                'queue_lengths': self.queue_lengths.copy(),
                'vehicles_processed': self.vehicles_processed.copy(),
                'green_phase': self.green_phase,
                'green_timer': self.green_timer,
                'simulator_type': 'mock'
            }
        else:
            return {
                'time': self.time,
                'step': self.step_count,
                'simulator_type': 'sumo',
                'connected': self.sumo_connected
            }
    
    def reset(self):
        """Reset simulation"""
        self.time = 0
        self.step_count = 0
        if self.use_mock:
            self._init_mock()
        else:
            if self.sumo_connected:
                traci.close()
            self._init_sumo()
    
    def close(self):
        """Close simulation connections"""
        if not self.use_mock and self.sumo_connected:
            traci.close()
            print("SUMO connection closed")

def run_simulation(duration=100, render=True):
    """Run a simple simulation"""
    print("\n" + "="*50)
    print("STARTING TRAFFIC SIMULATION")
    print("="*50 + "\n")
    
    # Create simulator (force mock for now to avoid SUMO issues)
    sim = TrafficSimulator(use_mock=True)
    
    # Run simulation
    for step in range(duration):
        # Random action for demo (0 or 1)
        action = random.choice([0, 1])
        
        state, reward = sim.step(action)
        
        # Print every 10 steps
        if step % 10 == 0:
            metrics = sim.get_metrics()
            print(f"Step {step:3d} | Time: {metrics['time']:4.1f}s | "
                  f"Total Wait: {metrics['total_waiting_time']:6.1f}s | "
                  f"Phase: {metrics['green_phase']} | "
                  f"State: {state}")
    
    # Final metrics
    print("\n" + "="*50)
    print("SIMULATION COMPLETE")
    print("="*50)
    final_metrics = sim.get_metrics()
    print(f"Total steps: {final_metrics['step']}")
    print(f"Total vehicles processed: {sum(final_metrics['vehicles_processed'].values())}")
    print(f"Final queue lengths: {final_metrics['queue_lengths']}")
    
    sim.close()
    return sim

if __name__ == "__main__":
    run_simulation()
