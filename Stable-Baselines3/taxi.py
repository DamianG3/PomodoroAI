import gymnasium as gym
env = gym.make('Taxi-v3', render_mode='ansi')
env.reset()

print(env.render())