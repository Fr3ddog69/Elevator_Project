from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.vec_env import DummyVecEnv
from MultiElevatorEnv import MultiElevatorEnv
import numpy as np


def make_env():
    return MultiElevatorEnv(
        num_elevators=1,
        num_floors=10,
        max_passengers=5,
        max_guests=80,
        spawn_intervall=120 * 60,
        working_time_mean=480 * 60,
        working_time_std=50 * 60,
        sim_step_size=1,
        ride_time=4,
        door_time=4,
    )


if __name__ == "__main__":
    env = DummyVecEnv(
        [
            lambda: ActionMasker(
                make_env(), action_mask_fn=MultiElevatorEnv.get_action_mask
            )
        ]
    )
    model = MaskablePPO.load(
        "checkpoints_episode/ppo_elevator_episode_1131.zip", env=env
    )

    obs = env.reset()  # Only one value!
    done = False
    episode_reward = 0
    _, info = env.envs[0].env.reset()
    # Get action mask (after reset there is no info in obs!)
    action_mask = info["action_mask"]
    print("Action_mask: ", action_mask)
    print("Action mask for this observation:\n", action_mask)
    while not done:
        action, _ = model.predict(obs, action_masks=action_mask, deterministic=True)
        # print("Action: ", action)

        obs, reward, done, info = env.step(action)
        episode_reward += reward[0]
        # Action mask for next step
        action_mask = info[0]["action_mask"]

        # print(f"Reward: {reward}")
        # print("Action_mask: ", action_mask)
    print(f"Total reward for this episode: {episode_reward}")
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.vec_env import DummyVecEnv
from MultiElevatorEnv import MultiElevatorEnv
import numpy as np


def make_env():
    return MultiElevatorEnv(
        num_elevators=1,
        num_floors=10,
        max_passengers=5,
        max_guests=80,
        spawn_intervall=120 * 60,
        working_time_mean=480 * 60,
        working_time_std=50 * 60,
        sim_step_size=1,
        ride_time=4,
        door_time=4,
    )


if __name__ == "__main__":
    env = DummyVecEnv(
        [
            lambda: ActionMasker(
                make_env(), action_mask_fn=MultiElevatorEnv.get_action_mask
            )
        ]
    )
    model = MaskablePPO.load(
        "checkpoints_episode/ppo_elevator_episode_1131.zip", env=env
    )

    obs = env.reset()  # Only one value!
    done = False
    episode_reward = 0
    _, info = env.envs[0].env.reset()
    # Get action mask (after reset there is no info in obs!)
    action_mask = info["action_mask"]
    print("Action_mask: ", action_mask)
    print("Action mask for this observation:\n", action_mask)
    while not done:
        action, _ = model.predict(obs, action_masks=action_mask, deterministic=True)
        # print("Action: ", action)

        obs, reward, done, info = env.step(action)
        episode_reward += reward[0]
        # Action mask for next step
        action_mask = info[0]["action_mask"]

        # print(f"Reward: {reward}")
        # print("Action_mask: ", action_mask)
    print(f"Total reward for this episode: {episode_reward}")
