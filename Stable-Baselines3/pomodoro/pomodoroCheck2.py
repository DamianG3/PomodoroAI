import time
from pomodoroEnv import PomodoroEnv

env = PomodoroEnv()
episodes = 5

for episode in range(episodes):
    terminated = False
    truncated = False
    obs = env.reset()
        
    while not terminated or not truncated:
        time.sleep(1.5)
        random_action = env.action_space.sample()
        print("action:",random_action)
        obs, reward, terminated, truncated, info = env.step(random_action)
        # print('reward',reward)
        env.render()