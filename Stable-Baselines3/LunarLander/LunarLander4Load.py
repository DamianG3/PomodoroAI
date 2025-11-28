import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")

import os
import gymnasium as gym
from stable_baselines3 import PPO # best for lunar landing
# from stable_baselines3 import A2C
# from stable_baselines3 import DQN

models_dir = "models/PPO"

# Create the environment
env = gym.make('LunarLander-v3', render_mode="human")
env.reset() # required before you can step the environment

model_path = f"{models_dir}/100000.zip"
model = PPO.load(model_path, env=env)

vec_env = model.get_env()

episodes = 5
rewards = [0]
for ep in range(episodes):
    print(f"\n\n{ep}. reward: {rewards[0]}")
    obs = vec_env.reset()
    done = False
    # print("Current reward: ")
    while not done:
        # pass observation to model to get predicted action
        action, _states = model.predict(obs, deterministic=True)

        # pass action to env and get info back
        obs, rewards, done, info = vec_env.step(action)
        # print(rewards[0])
 
        # show the environment on the screen
        env.render()
# print("TRAINING FINISHED")