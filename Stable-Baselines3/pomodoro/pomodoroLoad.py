import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")

import os
import time
import gymnasium as gym
from gymnasium.wrappers import RescaleAction
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.monitor import Monitor
from stable_baselines3 import SAC
from pomodoroEnv import PomodoroEnv

algorithm = "SAC"

models_dir = algorithm + "/models"
VecEnv_dir = algorithm + "/VecEnv"
logdir = "logs"

# Create the environment


def make_env():
    user_profile={
        "preferred_work_base": 25.0,
        "preferred_break_base": 5.0,
        "variability": 3.0,
        "early_stop_sensitivity": 0.10,
        "too_short_sensitivity": 0.07,
        "fatigue_influence": 0.8,
    }

    env = PomodoroEnv(
        # user_profile=user_profile
        )
    env = RescaleAction(env, -1, 1)
    env = Monitor(env)
    return env


env = DummyVecEnv([make_env])

vector_path = f"{VecEnv_dir}/10000.pkl"
env = VecNormalize.load(vector_path, env)

model_path = f"{models_dir}/10000.zip"
model = SAC.load(model_path, env=env)

env.reset() # required before you can step the environment

vec_env = model.get_env()

episodes = 5
for ep in range(episodes):
    obs = vec_env.reset()
    print("Observation:", obs)
    done = False
    while not done:
        time.sleep(2)
        # pass observation to model to get predicted action
        action, _states = model.predict(obs)

        
        print("Action:     ", action)
        # pass action to env and get info back
        obs, rewards, done, info = vec_env.step(action)

        print("Observation:", obs, "reward:", rewards, "\n")
 

# print("TRAINING FINISHED")