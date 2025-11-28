import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")

import gymnasium as gym
import time

# Create the environment
env = gym.make('LunarLander-v3', render_mode="human")
env.reset() # required before you can step the environment

# Environment Information
print("action space:", env.action_space) # Randomly sample an element of this space
print("sample action:", env.action_space.sample()) # Randomly sample an element of this space
print("observation space shape:", env.observation_space.shape)
# print("observation space:", env.observation_space)
print("sample observation:", env.observation_space.sample())

for step in range(100):
    # time.sleep(0.1)
    env.render()

    randomAction = env.action_space.sample()
    # # take random action
    observation, reward, terminated, truncated, info = env.step(randomAction)
    print()
    # print("observation:", observation, end='')
    print("reward:", reward, end=' ')
    print("terminated:", terminated, end=' ')
    print("truncated:", truncated, end=' ')
    print("info:", info)


env.close()