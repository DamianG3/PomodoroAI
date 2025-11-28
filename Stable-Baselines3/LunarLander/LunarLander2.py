import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")

import gymnasium as gym
from stable_baselines3 import PPO
# from stable_baselines3 import A2C
# from stable_baselines3 import DQN

# Create the environment
env = gym.make('LunarLander-v3', render_mode="human")
env.reset() # required before you can step the environment

# Train a model with a `stable_baselines3` algorithm
model = PPO('MlpPolicy', env, verbose=1, 
# Optional hyperparameters
    # seed = 33,
    # learning_rate = 0.001,
    # gamma = 0.999, # Discount factor
    # ent_coef = 0, #Entropy coefficient for the loss calculation
    )

model.learn(total_timesteps=10_000)
print("TRAINING FINISHED")
vec_env = model.get_env()


episodes = 10
rewards = [0]
for ep in range(episodes):
    print(f"\n\n{ep}. reward: {rewards[0]}")
    obs = vec_env.reset()
    done = False
    # print("Current reward: ")
    while not done:
        # pass observation to model to get predicted action
        action, _states = model.predict(obs, deterministic=True)
        model.learn(total_timesteps=1, reset_num_timesteps=False)


        # pass action to env and get info back
        obs, rewards, done, info = vec_env.step(action)
        # print(rewards[0])
 
        # show the environment on the screen
        env.render()


env.close()