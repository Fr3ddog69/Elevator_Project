from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.vec_env import SubprocVecEnv
from MultiElevatorEnv import MultiElevatorEnv
from episode_callback import StopTrainingOnEpisodes
from episodecheckpointcallback import EpisodeCheckpointCallback
from stable_baselines3.common.callbacks import CallbackList


def make_env():
    def _init():
        env = MultiElevatorEnv(
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
        return ActionMasker(env, action_mask_fn=MultiElevatorEnv.get_action_mask)

    return _init


if __name__ == "__main__":
    env = SubprocVecEnv([make_env() for _ in range(12)])

    # <-- Load model from last checkpoint here!
    last_checkpoint = "./checkpoints_episode/ppo_elevator_episode_1268.zip"
    model = MaskablePPO.load(last_checkpoint, env=env)

    n_episodes = 50  # or however many you want to continue training
    stop_callback = StopTrainingOnEpisodes(n_episodes=n_episodes, verbose=1)
    episode_checkpoint = EpisodeCheckpointCallback(
        save_path="./checkpoints_episode", name_prefix="ppo_elevator"
    )
    callback = CallbackList([stop_callback, episode_checkpoint])

    # Now call learn() again, with "reset_num_timesteps=False"!
    total_timesteps = int(1e8)  # or as many as you want to continue
    model.learn(
        total_timesteps=total_timesteps,
        callback=callback,
        tb_log_name="PPO_MultiElevator",
        reset_num_timesteps=False,  # IMPORTANT for continuing training!
    )

    save_path = "ppo_maskable_elevator_model"
    model.save(save_path)
    print(f"Training finished, model saved at: {save_path}")
