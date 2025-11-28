'''
To start server:
> `uvicorn main2:app --reload`
To stop the server, kill the terminal

http://127.0.0.1:8000/docs - Swagger

'''
# -------------------------------------------------------------
#                      Satable Baselines3
# -------------------------------------------------------------
from pomodoro.pomodoroEnv import PomodoroEnv
import numpy as np
from gymnasium.wrappers import RescaleAction
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.monitor import Monitor
from stable_baselines3 import SAC


step = 10000
# algorithm = "PPO"
algorithm = "SAC"
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
model = SAC.load(model_path, env=env)

envRoot = PomodoroEnv()

min_work, max_work = envRoot.min_work, envRoot.max_work
min_break, max_break = envRoot.min_break, envRoot.max_break

# -------------------------------------------------------------
#                          BACKEND
# -------------------------------------------------------------
from pydantic import BaseModel, Field
from fastapi import FastAPI

app = FastAPI()

# Pydantic model for item data
class Pomo(BaseModel):
    work: int
    break_: int = Field(alias="break")
    # model_config = {"populate_by_name": True}

class Observation(BaseModel):
	fatigue: int
	work_minutes_day: int
	break_minutes_day: int



@app.post("/pomodoro", response_model=Pomo)
def function_name(data: Observation):

    obs_real = np.array([[
         data.fatigue, 
         data.work_minutes_day, 
         data.break_minutes_day
        ]], dtype=np.float32)
    obs_norm = env.normalize_obs(obs_real)
    action_norm, _states = model.predict(obs_norm, )
    a = action_norm[0]

    work_real  = min_work  + (a[0] + 1) * 0.5 * (max_work  - min_work)
    break_real = min_break + (a[1] + 1) * 0.5 * (max_break - min_break)

    # print('obs_real:', obs_real)
    # print('obs_norm:', obs_norm)
    # print("action_norm:",  action_norm[0])
    # print("action_real:", work_real, break_real)


    return {"work": int(work_real), "break": int(break_real)}
