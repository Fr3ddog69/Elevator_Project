from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker

from stable_baselines3.common.vec_env import SubprocVecEnv  # <- IMPORTANT!
from stable_baselines3.common.callbacks import CallbackList
from MultiElevatorEnv import MultiElevatorEnv
from episode_callback import StopTrainingOnEpisodes
from episodecheckpointcallback import EpisodeCheckpointCallback


def make_env():
    # This function MUST be top-level, NO lambda!
    def _init():
        env = MultiElevatorEnv(
            num_elevators=1,
            num_floors=6,
            max_passengers=5,
            max_guests=50,
            spawn_intervall=10 * 60,
            working_time_mean=480 * 60,
            working_time_std=50 * 60,
            sim_step_size=1,
            ride_time=4,
            door_time=4,
            episodes_so_far=0,
        )
        # ActionMasker wrapping HERE!
        return ActionMasker(env, action_mask_fn=MultiElevatorEnv.get_action_mask)

    return _init


if __name__ == "__main__":
    # List of top-level initializers:
    env = SubprocVecEnv([make_env() for _ in range(12)])

    model = MaskablePPO(
        "MlpPolicy",
        env,
        verbose=1,
        tensorboard_log="./ppo_elevator_tensorboard/",
    )

    n_episodes = 500
    stop_callback = StopTrainingOnEpisodes(n_episodes=n_episodes, verbose=1)

    # Episode checkpoint after EACH episode!
    episode_checkpoint = EpisodeCheckpointCallback(
        save_path="./checkpoints_episode", name_prefix="ppo_elevator"
    )

    callback = CallbackList([stop_callback, episode_checkpoint])

    total_timesteps = int(1e8)
    model.learn(
        total_timesteps=total_timesteps,
        callback=callback,
        tb_log_name="PPO_MultiElevator",
    )

    save_path = "ppo_maskable_elevator_model"
    model.save(save_path)
    print(f"Training finished, model saved at: {save_path}")
