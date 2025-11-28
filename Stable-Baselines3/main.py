'''
To start server:
> `uvicorn main:app --reload`
To stop the server, kill the terminal

http://127.0.0.1:8000/doc - Swagger

'''
from pydantic import BaseModel, Field
from fastapi import FastAPI
from pomodoro.pomodoroEnv import PomodoroEnv


app = FastAPI()

env = PomodoroEnv()

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

    random_action = env.action_space.sample()

    print(random_action)

    return {"work": int(random_action[0]), "break": int(random_action[1])}
