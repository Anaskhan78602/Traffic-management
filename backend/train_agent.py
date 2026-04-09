"""
Train Q-learning agent for traffic signal control
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from simulator.core import TrafficSimulator
from ai.q_learning import QLearningTrafficAgent, TrafficEnvironment
import time

# 🔥 IMPORT SHARED STATE
from api_server import ai_training_data

# Safe matplotlib import
try:
    import matplotlib.pyplot as plt
    PLOT_AVAILABLE = True
except:
    PLOT_AVAILABLE = False


def train_agent(episodes=50, steps_per_episode=500, render_plot=True):
    print("\n" + "="*60)
    print("TRAINING Q-LEARNING TRAFFIC AGENT")
    print("="*60)

    agent = QLearningTrafficAgent(
        state_size=4,
        action_size=2,
        learning_rate=0.1,
        discount_factor=0.95,
        epsilon=0.3,
        epsilon_decay=0.99,
        min_epsilon=0.01
    )

    episode_rewards = []
    episode_wait_times = []

    start_time = time.time()

    for episode in range(episodes):
        sim = TrafficSimulator(use_mock=True)
        env = TrafficEnvironment(sim)

        state = env.reset()
        total_reward = 0
        total_wait_time = 0
        step_count = 1

        print(f"\nEpisode {episode + 1}/{episodes}")
        print("-" * 40)

        for step in range(steps_per_episode):
            action = agent.get_action(state, training=True)

            next_state, reward, done = env.step(action)

            agent.learn(state, action, reward, next_state, done)

            total_reward += reward
            state = next_state
            step_count = step + 1

            metrics = env.get_metrics()
            total_wait_time = metrics.get('total_waiting_time', 0)

            # 🔥 LIVE UPDATE TO FRONTEND
            avg_wait = total_wait_time / max(step_count, 1)

            ai_training_data["episode"] = episode + 1
            ai_training_data["total_reward"] = total_reward
            ai_training_data["avg_wait_time"] = avg_wait
            ai_training_data["epsilon"] = agent.epsilon
            ai_training_data["q_table_size"] = len(agent.q_table)
            ai_training_data["step"] = step + 1
            ai_training_data["episode_complete"] = False

            if (step + 1) % 100 == 0:
                print(f"Step {step+1:4d} | Action: {action} | "
                      f"Wait: {total_wait_time:.1f}s | Reward: {reward:.1f}")

            if done:
                break

        agent.decay_epsilon()

        episode_rewards.append(total_reward)
        episode_wait_times.append(total_wait_time)

        avg_wait = total_wait_time / max(step_count, 1)

        print(f"✓ Episode {episode + 1} complete")
        print(f"  Total reward: {total_reward:.1f}")
        print(f"  Avg wait time: {avg_wait:.1f}s")
        print(f"  Epsilon: {agent.epsilon:.3f}")
        print(f"  Q-table size: {len(agent.q_table)}")

        # 🔥 MARK EPISODE COMPLETE (IMPORTANT FOR FRONTEND TIMELINE)
        ai_training_data["episode_complete"] = True

        env.close()

        # 🔥 RESET FLAG (next loop tick)
        ai_training_data["episode_complete"] = False

    training_time = time.time() - start_time

    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print(f"Training time: {training_time:.1f} sec")

    os.makedirs("models", exist_ok=True)
    agent.save_model("models/trained_q_table.pkl")

    if render_plot and PLOT_AVAILABLE:
        plot_training_results(episode_rewards, episode_wait_times)

    return agent


def plot_training_results(rewards, wait_times):
    try:
        plt.figure()

        plt.subplot(2, 1, 1)
        plt.plot(rewards)
        plt.title("Rewards")

        plt.subplot(2, 1, 2)
        plt.plot(wait_times)
        plt.title("Waiting Time")

        plt.tight_layout()
        plt.savefig("training_results.png")
        print("✓ Plot saved")

        plt.show()

    except Exception as e:
        print("Plot error:", e)


def test_trained_agent(agent, episodes=3):
    print("\nTesting trained agent")

    for episode in range(episodes):
        sim = TrafficSimulator(use_mock=True)
        env = TrafficEnvironment(sim)

        state = env.reset()

        for step in range(200):
            action = agent.get_best_action(state)
            next_state, _, done = env.step(action)
            state = next_state

            if done:
                break

        env.close()

    print("Testing complete")


if __name__ == "__main__":
    agent = train_agent(episodes=20, steps_per_episode=300)
    test_trained_agent(agent)

    print("\nDONE")