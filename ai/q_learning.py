"""
Q-Learning Agent for Traffic Signal Control
"""

import numpy as np
from collections import defaultdict
import pickle
import os

class QLearningTrafficAgent:
    def __init__(self, 
                 state_size=4,  # 4 approaches (N, S, E, W)
                 action_size=2,  # 0: keep, 1: switch
                 learning_rate=0.1,
                 discount_factor=0.95,
                 epsilon=0.1,
                 epsilon_decay=0.995,
                 min_epsilon=0.01):
        
        self.q_table = defaultdict(lambda: np.zeros(action_size))
        self.state_size = state_size
        self.action_size = action_size
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon
        
        # Statistics
        self.episode_rewards = []
        self.episode_lengths = []
        
    def get_action(self, state, training=True):
        """Choose action using epsilon-greedy policy"""
        if training and np.random.random() < self.epsilon:
            return np.random.randint(self.action_size)  # Explore
        else:
            return np.argmax(self.q_table[state])  # Exploit
    
    def learn(self, state, action, reward, next_state, done=False):
        """Update Q-table using Q-learning algorithm"""
        current_q = self.q_table[state][action]
        best_next_q = np.max(self.q_table[next_state])
        
        # Q-learning update formula
        new_q = current_q + self.lr * (reward + self.gamma * best_next_q - current_q)
        self.q_table[state][action] = new_q
        
    def decay_epsilon(self):
        """Decay exploration rate"""
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
    
    def save_model(self, filepath="models/q_table.pkl"):
        """Save Q-table to file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(dict(self.q_table), f)
        print(f"✓ Model saved to {filepath}")
    
    def load_model(self, filepath="models/q_table.pkl"):
        """Load Q-table from file"""
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                loaded_dict = pickle.load(f)
                self.q_table = defaultdict(lambda: np.zeros(self.action_size), loaded_dict)
            print(f"✓ Model loaded from {filepath}")
            return True
        return False
    
    def get_best_action(self, state):
        """Get best action without exploration"""
        return np.argmax(self.q_table[state])
    
    def get_stats(self):
        """Get agent statistics"""
        return {
            'epsilon': self.epsilon,
            'q_table_size': len(self.q_table),
            'avg_reward': np.mean(self.episode_rewards[-10:]) if self.episode_rewards else 0
        }

class TrafficEnvironment:
    """Wrapper for simulator to work with Q-learning"""
    
    def __init__(self, simulator):
        self.sim = simulator
        self.steps = 0
        
    def reset(self):
        """Reset environment"""
        self.sim.reset()
        self.steps = 0
        return self.sim._get_state()
    
    def step(self, action):
        """Execute action and return (next_state, reward, done)"""
        next_state, reward = self.sim.step(action)
        self.steps += 1
        
        # Check if episode is done (e.g., max steps or no vehicles)
        done = self.steps >= 3600  # 1 hour max
        if done:
            print(f"Episode finished after {self.steps} steps")
        
        return next_state, reward, done
    
    def get_metrics(self):
        """Get current metrics"""
        return self.sim.get_metrics()
    
    def close(self):
        """Close environment"""
        self.sim.close()
