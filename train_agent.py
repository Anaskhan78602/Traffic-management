#!/usr/bin/env python3
"""
Train Q-learning agent for traffic signal control
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from simulator.core import TrafficSimulator
from ai.q_learning import QLearningTrafficAgent, TrafficEnvironment
import time
import matplotlib.pyplot as plt

def train_agent(episodes=50, steps_per_episode=500, render_plot=True):
    """Train the Q-learning agent"""
    
    print("\n" + "="*60)
    print("TRAINING Q-LEARNING TRAFFIC AGENT")
    print("="*60)
    
    # Initialize agent and environment
    agent = QLearningTrafficAgent(
        state_size=4,
        action_size=2,
        learning_rate=0.1,
        discount_factor=0.95,
        epsilon=0.3,  # Start with higher exploration
        epsilon_decay=0.99,
        min_epsilon=0.01
    )
    
    episode_rewards = []
    episode_wait_times = []
    
    start_time = time.time()
    
    for episode in range(episodes):
        # Create new simulator instance
        sim = TrafficSimulator(use_mock=True)
        env = TrafficEnvironment(sim)
        
        state = env.reset()
        total_reward = 0
        total_wait_time = 0
        step_count = 0
        
        print(f"\n📊 Episode {episode + 1}/{episodes}")
        print("-" * 40)
        
        for step in range(steps_per_episode):
            # Get action from agent
            action = agent.get_action(state, training=True)
            
            # Execute action
            next_state, reward, done = env.step(action)
            
            # Learn from experience
            agent.learn(state, action, reward, next_state, done)
            
            # Update tracking
            total_reward += reward
            state = next_state
            step_count = step
            
            # Get metrics
            metrics = env.get_metrics()
            total_wait_time = metrics.get('total_waiting_time', 0)
            
            # Print progress every 100 steps
            if (step + 1) % 100 == 0:
                print(f"  Step {step+1:4d} | Action: {action} | "
                      f"Wait: {total_wait_time:.1f}s | "
                      f"Reward: {reward:.1f}")
            
            if done:
                break
        
        # Decay epsilon after each episode
        agent.decay_epsilon()
        
        # Record statistics
        episode_rewards.append(total_reward)
        episode_wait_times.append(total_wait_time)
        
        print(f"✓ Episode {episode + 1} complete:")
        print(f"  Total reward: {total_reward:.1f}")
        print(f"  Avg wait time: {total_wait_time/step_count:.1f}s")
        print(f"  Epsilon: {agent.epsilon:.3f}")
        print(f"  Q-table size: {len(agent.q_table)}")
        
        env.close()
    
    training_time = time.time() - start_time
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print(f"Training time: {training_time:.1f} seconds")
    print(f"Final epsilon: {agent.epsilon:.3f}")
    print(f"Final Q-table size: {len(agent.q_table)}")
    
    # Save the trained model
    agent.save_model("models/trained_q_table.pkl")
    
    # Plot results
    if render_plot:
        plot_training_results(episode_rewards, episode_wait_times)
    
    return agent, episode_rewards, episode_wait_times

def plot_training_results(rewards, wait_times):
    """Plot training progress"""
    try:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Plot rewards
        ax1.plot(rewards)
        ax1.set_xlabel('Episode')
        ax1.set_ylabel('Total Reward')
        ax1.set_title('Training Progress - Episode Rewards')
        ax1.grid(True)
        
        # Plot waiting times
        ax2.plot(wait_times)
        ax2.set_xlabel('Episode')
        ax2.set_ylabel('Total Waiting Time (s)')
        ax2.set_title('Training Progress - Waiting Time')
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig('training_results.png', dpi=100)
        print("✓ Training plot saved to training_results.png")
        plt.show()
    except Exception as e:
        print(f"Plotting error: {e}")

def test_trained_agent(agent, episodes=3):
    """Test the trained agent"""
    print("\n" + "="*60)
    print("TESTING TRAINED AGENT")
    print("="*60)
    
    total_wait_times = []
    
    for episode in range(episodes):
        sim = TrafficSimulator(use_mock=True)
        env = TrafficEnvironment(sim)
        
        state = env.reset()
        episode_wait = 0
        
        print(f"\nTest Episode {episode + 1}")
        print("-" * 30)
        
        for step in range(200):
            # Use best action (no exploration)
            action = agent.get_best_action(state)
            next_state, reward, done = env.step(action)
            state = next_state
            
            metrics = env.get_metrics()
            episode_wait = metrics.get('total_waiting_time', 0)
            
            if (step + 1) % 50 == 0:
                print(f"  Step {step+1:3d} | Wait: {episode_wait:.1f}s | "
                      f"Phase: {metrics.get('green_phase', 'N/A')}")
            
            if done:
                break
        
        total_wait_times.append(episode_wait)
        print(f"✓ Test {episode + 1} complete - Total wait: {episode_wait:.1f}s")
        env.close()
    
    avg_wait = sum(total_wait_times) / len(total_wait_times)
    print(f"\n📊 Average waiting time: {avg_wait:.1f}s")
    
    return avg_wait

if __name__ == "__main__":
    # Train the agent
    agent, rewards, wait_times = train_agent(episodes=20, steps_per_episode=300)
    
    # Test the trained agent
    test_trained_agent(agent, episodes=3)
    
    print("\n✅ Agent training complete!")
    print("Next steps:")
    print("1. Run: python3 evaluate_agent.py  # Compare with fixed timing")
    print("2. Run: python3 api_server.py       # Start FastAPI backend")
