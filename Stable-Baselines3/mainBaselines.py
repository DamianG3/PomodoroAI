from pomodoro.pomodoroEnv import PomodoroEnv

import numpy as np
from gymnasium.wrappers import RescaleAction
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.monitor import Monitor
from stable_baselines3 import PPO 
# -------------------------------------------------------------
#                      Satable Baselines3
# -------------------------------------------------------------

step = 10000
algorithm = "PPO"
models_dir = 'pomodoro/' + algorithm + "/models"
VecEnv_dir = 'pomodoro/' + algorithm + "/VecEnv"

def make_env():
    env = PomodoroEnv()
    env = RescaleAction(env, -1, 1)
    env = Monitor(env)
    return env

env = DummyVecEnv([make_env])
vector_path = f"{VecEnv_dir}/{step}.pkl"
env = VecNormalize.load(vector_path, env)
model_path = f"{models_dir}/{step}.zip"
model = PPO.load(model_path, env=env)



obs_real = np.array([[3, 185, 62]], dtype=np.float32)
obs_norm = env.normalize_obs(obs_real)
print('obs_real:', obs_real)
print('obs_norm:', obs_norm)

action_norm, _states = model.predict(obs_norm, deterministic=True)
print("action_norm:",  action_norm[0])

a = action_norm[0]

envRoot = PomodoroEnv()

min_work, max_work = envRoot.min_work, envRoot.max_work
min_break, max_break = envRoot.min_break, envRoot.max_break

work_real  = min_work  + (a[0] + 1) * 0.5 * (max_work  - min_work)
break_real = min_break + (a[1] + 1) * 0.5 * (max_break - min_break)

print("action_real:", work_real, break_real)