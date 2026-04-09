"""
Compare AI agent performance against fixed timing baseline
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from simulator.core import TrafficSimulator
from backend.ai.q_learning import QLearningTrafficAgent


def run_fixed_timing(duration=500):
    print("\nRunning FIXED TIMING simulation...")

    sim = TrafficSimulator(use_mock=True)
    total_wait = 0
    step_count = 1  # FIX: avoid divide by zero

    for step in range(duration):
        cycle_position = step % 60

        if cycle_position < 30:
            sim.green_phase = 'NS'
        else:
            sim.green_phase = 'EW'

        _, reward = sim.step(0)
        total_wait += -reward
        step_count = step + 1

        if (step + 1) % 100 == 0:
            print(f"Step {step+1}: Total wait = {total_wait:.1f}s")

    avg_wait = total_wait / max(step_count, 1)
    sim.close()

    print("\n✓ Fixed timing complete:")
    print(f"Total waiting time: {total_wait:.1f}s")
    print(f"Average wait per step: {avg_wait:.1f}s")

    return total_wait, avg_wait


def run_ai_controlled(agent, duration=500):
    print("\nRunning AI-CONTROLLED simulation...")

    sim = TrafficSimulator(use_mock=True)
    total_wait = 0
    step_count = 1

    for step in range(duration):
        try:
            state = sim._get_state()
        except:
            state = (0, 0, 0, 0)  # fallback safety

        action = agent.get_best_action(state)

        _, reward = sim.step(action)
        total_wait += -reward
        step_count = step + 1

        if (step + 1) % 100 == 0:
            print(f"Step {step+1}: Wait = {total_wait:.1f}s | Action = {action}")

    avg_wait = total_wait / max(step_count, 1)
    sim.close()

    print("\n✓ AI control complete:")
    print(f"Total waiting time: {total_wait:.1f}s")
    print(f"Average wait per step: {avg_wait:.1f}s")

    return total_wait, avg_wait


def main():
    print("\n" + "="*60)
    print("AI vs FIXED TIMING COMPARISON")
    print("="*60)

    agent = QLearningTrafficAgent()

    # Ensure model exists
    if os.path.exists("models/trained_q_table.pkl") and agent.load_model("models/trained_q_table.pkl"):
        print("✓ Loaded trained agent")
    else:
        print("No trained agent found, training one now...")
        from backend.train_agent import train_agent
        agent = train_agent(episodes=10, steps_per_episode=300, render_plot=False)

    # Run simulations
    fixed_total, fixed_avg = run_fixed_timing(duration=500)
    ai_total, ai_avg = run_ai_controlled(agent, duration=500)

    # Safe improvement calculation
    if fixed_avg == 0:
        improvement = 0
    else:
        improvement = ((fixed_avg - ai_avg) / fixed_avg) * 100

    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    print(f"Fixed Timing Avg Wait: {fixed_avg:.1f}s")
    print(f"AI Controlled Avg Wait: {ai_avg:.1f}s")
    print(f"Improvement: {improvement:.1f}%")
    print("="*60)

    if improvement >= 10:
        print("SUCCESS! Met 10% improvement target")
    else:
        print(f"Need {10 - improvement:.1f}% more improvement")

    return improvement


if __name__ == "__main__":
    main()