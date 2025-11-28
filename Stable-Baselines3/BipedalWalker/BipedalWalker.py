import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")

import os
import gymnasium as gym
from stable_baselines3 import PPO # best for lunar landing
# from stable_baselines3 import A2C
# from stable_baselines3 import DQN

algorithm = "PPO"

models_dir = "models/" + algorithm
logdir = "logs"
#C:> tensorboard --logdir=logs

if not os.path.exists(models_dir):
    os.makedirs(models_dir)

if not os.path.exists(logdir):
    os.makedirs(logdir)

# Create the environment
env = gym.make("BipedalWalker-v3", hardcore=False, render_mode="human")
env.reset() # required before you can step the environment

# Train a model with a `stable_baselines3` algorithm
model = PPO('MlpPolicy', env, verbose=1, tensorboard_log=logdir, 
# Optional hyperparameters
    # seed = 33,
    # learning_rate = 0.001,
    # gamma = 0.999, # Discount factor
    # ent_coef = 0, #Entropy coefficient for the loss calculation
    )


TIMESTEPS = 10_000
iters = 0
while True:
    iters += 1
    
    # model.learn(total_timesteps=10_000)
    model.learn(total_timesteps=TIMESTEPS, reset_num_timesteps=False, tb_log_name=algorithm)
    model.save(f"{models_dir}/{TIMESTEPS*iters}")


# print("TRAINING FINISHED")