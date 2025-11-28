import gymnasium as gym
from gymnasium import spaces
import numpy as np

class CounterEnv(gym.Env):


    def __init__(self):
        super().__init__()

        # "State"
        # Observation space: Beween -5 and 5
        self.observation_space = spaces.Box(low=-5, high=5, shape=(1,))
        
        # Action space: 0 = decrement, 1 = increment
        self.action_space = spaces.Discrete(2)



        self.state = 0

    def reset(self, seed=None, options=None):
        """Starts a new episode and returns the initial observation."""
        super().reset(seed=seed)
        self.state = 0  # reset the counter

        observation = np.array([self.state], dtype=np.int32)
        info = {}
        return observation, info

    def step(self, action):
        """Takes an action and returns (observation, reward, terminated, truncated, info)."""
        # Apply the action
        if action == 1:
            self.state += 1
        else:
            self.state -= 1

        # Reward for moving toward +5
        reward = float(self.state)

        # Episode ends when reaching the bounds
        terminated = abs(self.state) >= 5
        truncated = False  # we are not using time limits here

        observation = np.array([self.state], dtype=np.int32)
        info = {}

        return observation, reward, terminated, truncated, info
