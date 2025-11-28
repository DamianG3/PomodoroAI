"""
pomodoro_env.py

A Gymnasium environment to personalize Pomodoro timings.

State (obs):
 - fatigue: float in [0,5]
 - total_work_today (minutes): float in [0, max_work_minutes]
 - total_break_today (minutes): float in [0, max_break_minutes]

Action:
 - Box(2): [work_minutes, break_minutes]
   work_minutes in [15, 50]
   break_minutes in [5, 20]

Reward:
 - Negative if user stops work timer early (user couldn't maintain the suggested work time).
 - Negative if user reports "work time too short" (recommended too short compared to user's preference).
 - Otherwise positive reward proportional to adherence/productivity and penalize extremely long sessions that harm fatigue.
"""

from typing import Tuple, Dict, Optional
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from gymnasium.utils import seeding


class PomodoroEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        *,
        # Observation
        max_work_minutes_day: int = 8 * 60,      # upper bound for total work tracked (minutes)
        max_break_minutes_day: int = 3 * 60,     # upper bound for total break tracked (minutes)
        min_fatigue: float = 1.0,
        max_fatigue: float = 5.0,

        # Action
        min_work: int = 15,
        max_work: int = 50,
        min_break: int = 5,
        max_break: int = 20,

        # Reward
        early_stop_penalty: float = -2.0,
        too_short_penalty: float = -1.0,
        adherence_reward: float = 2.0,
        fatigue_cost_per_min: float = -0.005,

        max_steps_per_episode: int = 50,         # number of Pomodoros per episode (day)
        
        user_profile: Optional[dict] = None,     # parameters controlling simulated user's behavior
    ):
        super().__init__()

        # Validations
        assert min_fatigue < max_fatigue, "Invalid fatigue range: min_fatigue must be < max_fatigue"
        assert min_work < max_work, "Invalid work range: min_work must be < max_work"
        assert min_break < max_break, "Invalid break range: min_break must be < max_break"
        assert max_steps_per_episode > 0, "Invalid max steps per episode: max_steps_per_episode must be > 0"

        # Action space: [work_minutes, break_minutes]
        self.min_work = min_work
        self.max_work = max_work
        self.min_break = min_break
        self.max_break = max_break
        self.action_space = spaces.Box(
            low=np.array([self.min_work, self.min_break], dtype=np.float32),
            high=np.array([self.max_work, self.max_break], dtype=np.float32),
            dtype=np.float32,
        )

        # Observation space: [fatigue, total_work_today, total_break_today]
        self.min_fatigue = min_fatigue
        self.max_fatigue = max_fatigue
        self.max_work_minutes_day = max_work_minutes_day
        self.max_break_minutes_day = max_break_minutes_day
        self.observation_space = spaces.Box(
            low=np.array([self.min_fatigue, 0.0, 0.0], dtype=np.float32),
            high=np.array([self.max_fatigue, float(self.max_work_minutes_day), float(self.max_break_minutes_day)], dtype=np.float32),
            dtype=np.float32,
        )

        # Reward parameters
        self.early_stop_penalty = early_stop_penalty
        self.too_short_penalty = too_short_penalty
        self.adherence_reward = adherence_reward
        self.fatigue_cost_per_min = fatigue_cost_per_min

        # Episode progress
        self.max_steps_per_episode = max_steps_per_episode
        self.current_step = 0

        # User model parameters (stochastic)
        # - preferred_work_base: user's baseline preferred work length (minutes)
        # - preferred_break_base: user's baseline preferred break length (minutes)
        # - variability: how much user's preference fluctuates across the day
        # - early_stop_sensitivity: how likely the user is to stop early when fatigued or when recommended too long
        # - too_short_sensitivity: how likely user says "too short" when recommended shorter than preference
        # - fatigue_influence: how likely user’s current fatigue level increases the probability of stopping work early
        if user_profile is None:
            user_profile = {
                "preferred_work_base": 25.0,
                "preferred_break_base": 5.0,
                "variability": 4.0,
                "early_stop_sensitivity": 0.12,
                "too_short_sensitivity": 0.10,
                "fatigue_influence": 0.7,
            }
        self.user_profile = user_profile

        # # Seeding
        # self.np_random, seed = seeding.np_random(seed)
        # self._seed = seed

        # Internal state
        # self.state = None  # (fatigue, total_work_today, total_break_today)
        # self.terminated = False
        # self.truncated = False

    def reset(self, seed: Optional[int] = None):
        # if seed is not None:
        #     self.np_random, _ = seeding.np_random(seed)

        self.np_random, seed = seeding.np_random(seed)
        self._seed = seed

        # Start the day with some random baseline fatigue
        baseline_fatigue = float(self.np_random.uniform(self.min_fatigue, self.max_fatigue))
        self.state = np.array([baseline_fatigue, 0.0, 0.0], dtype=np.float32)

        self.current_step = 0
        self.terminated = False
        self.truncated = False

        obs = self._get_obs()
        info = {}
        return obs, info

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, dict]:
        """
        action: [work_minutes, break_minutes] (floats)
        returns: obs, reward, terminated, truncated, info
        """

        # Validations
        assert self.action_space.contains(action), f"Action {action} is out of bounds."
        recommended_work = float(np.clip(action[0], self.min_work, self.max_work))
        recommended_break = float(np.clip(action[1], self.min_break, self.max_break))

        fatigue, total_work, total_break = self.state.copy() # self.state is a numpy array

        # Simulate the user's actual behavior during this Pomodoro
        actual_work_minutes, actual_break_minutes, user_report, newFatigue = self._simulate_user_response(
            recommended_work,
            recommended_break,
            fatigue,
        )
        # user_report is dict: {"stopped_early":bool, "too_short":bool}

        # Update totals
        total_work += actual_work_minutes
        total_break += actual_break_minutes

        # Update state
        self.state = np.array([newFatigue, total_work, total_break], dtype=np.float32)

        # Compute reward
        reward = self._compute_reward(
            recommended_work=recommended_work,
            actual_work=actual_work_minutes,
            user_report=user_report,
            fatigue=newFatigue,
        )

        # Step counters & termination
        self.current_step += 1
        # truncated if day over daily budget, terminated if reached max steps
        truncated = False
        terminated = False
        if (total_work >= self.max_work_minutes_day) or (total_break >= self.max_break_minutes_day):
            truncated = True
        if self.current_step >= self.max_steps_per_episode:
            terminated = True

        self.terminated = terminated
        self.truncated = truncated

        obs = self._get_obs()
        info = {
            "recommended_work": recommended_work,
            "recommended_break": recommended_break,
            "actual_work": actual_work_minutes,
            "actual_break": actual_break_minutes,
            "user_report": user_report,
        }
        return obs, float(reward), bool(terminated), bool(truncated), info

    # --------------------
    # Helpers
    # --------------------
    def _get_obs(self) -> np.ndarray:
        return self.state.copy()

    def _simulate_user_response(
        self,
        recommended_work: float,
        recommended_break: float,
        fatigue: float,
    ) -> Tuple[float, float, dict]:
        """
        Stochastic user model

        Returns:
          actual_work_minutes, actual_break_minutes, user_report
        user_report: {"stopped_early": bool, "too_short": bool}
        """
        p = self.user_profile

        # Simulated variation in user’s preferred work duration
        pref_noise = self.np_random.normal(scale=p["variability"])
        preferred_work = max(5.0, p["preferred_work_base"] + pref_noise) 
            # at least can work 5 minutes

        # Preferred break
        pref_break_noise = self.np_random.normal(scale=max(1.0, p["variability"] / 3))
        preferred_break = max(1.0, p["preferred_break_base"] + pref_break_noise)
            # at least needs 1 minute rest

        fatigue_factor = fatigue / self.max_fatigue
        
        # Early-stop probability increases if:
        # - fatigue is high
        # - recommended_work >> preferred_work

        # The exact amount recomended (very unlikely)
        if recommended_work == preferred_work: 
            stopped_early = False
            reported_too_short = False

        # Too long
        elif recommended_work > preferred_work: 
            
            length_mismatch = (recommended_work - preferred_work) / preferred_work

            early_stop_prob = p["early_stop_sensitivity"] * (1.0 + fatigue_factor * p["fatigue_influence"]) + 0.9 * length_mismatch
            early_stop_prob = float(np.clip(early_stop_prob, 0.0, 0.95))

            stopped_early = self.np_random.random() < early_stop_prob
            reported_too_short = False

        # Too short
        elif recommended_work < preferred_work: 
            length_mismatch = (preferred_work - recommended_work) / preferred_work

            too_short_prob = p["too_short_sensitivity"] * length_mismatch * (1.0 + 0.5 * self.np_random.random())
            too_short_prob = float(np.clip(too_short_prob, 0.0, 0.95))

            stopped_early = False
            reported_too_short = self.np_random.random() < too_short_prob


        # Work calculation
        if stopped_early:
            # fraction left: if fatigued, more likely to stop sooner
            frac = max(0.15, 1.0 - 0.5 * fatigue_factor - 0.4 * self.np_random.random())
            actual_work = max(1.0, recommended_work * frac)
        else:
            # user tries to stick to recommended_work but with slight noise
            actual_work = float(np.clip(
                self.np_random.normal(loc=recommended_work, scale=2.0), 
                1.0, # at least works 5 minutes
                recommended_work + 5.0 # At most works 5 minutes more
            ))

        # Break calculation
        actual_break = float(np.clip(
            self.np_random.normal(loc=recommended_break, scale=1.0), 
            0.0, 
            recommended_break + 3.0))

        # Update fatigue
        # - fatigue increases with work minutes and decreases a bit with break minutes.
        fatigue_change = (actual_work / 60.0) * 1.0 - (actual_break / 60.0) * 0.6
        # scale down so fatigue is bounded 0-5 reasonably
        fatigue = float(np.clip(fatigue + fatigue_change, self.min_fatigue, self.max_fatigue))

        user_report = {"stopped_early": bool(stopped_early), "too_short": bool(reported_too_short)}
        return float(actual_work), float(actual_break), user_report, fatigue

    def _compute_reward(
        self,
        recommended_work: float,
        actual_work: float,
        user_report: dict,
        fatigue: float,
    ) -> float:
        """
        Reward logic:
          - If user stopped early => negative large penalty (user dissatisfaction / lower productivity).
          - If user reported "too short" => small negative penalty.
          - If adhered (actual_work approx recommended_work and not reported too short) => positive reward.
          - Fatigue cost: small negative reward proportional to work_minutes (encourages not exhausting the user).
        """
        reward = 0.0
    
        if user_report.get("stopped_early", False):
            # Strong negative reward on early stop
            reward += self.early_stop_penalty
        elif user_report.get("too_short", False):
            # Mild negative if user says work was too short
            reward += self.too_short_penalty
        else:
            # Positive reward for adherence (closer actual to recommended yields larger reward)
            adherence_ratio = min(1.0, actual_work / recommended_work)
            reward += self.adherence_reward * adherence_ratio

        # Penalize building too much fatigue: per-minute cost (small)
        # reward += self.fatigue_cost_per_min * work_minutes
        reward += -1.5 * (fatigue / self.max_fatigue)

        return float(reward)


    def render(self):
        fatigue, total_work, total_break = self.state
        print(f"[PomodoroEnv] step={self.current_step} fatigue={fatigue:.2f} total_work={total_work:.1f}m total_break={total_break:.1f}m")


    # def seed(self, seed: Optional[int] = None):
    #     self.np_random, seed = seeding.np_random(seed)
    #     self._seed = seed
    #     return [seed]
