from stable_baselines3.common.callbacks import BaseCallback


class EpisodeCheckpointCallback(BaseCallback):
    """
    Saves a model checkpoint after each episode.
    """

    def __init__(self, save_path, name_prefix="model", verbose=0):
        super().__init__(verbose)
        self.save_path = save_path
        self.name_prefix = name_prefix
        self.episode_counter = 1268

    def _on_step(self) -> bool:
        dones = self.locals.get("dones")
        if dones is not None:
            for done in dones:
                if done:
                    self.episode_counter += 1
                    print(f"[CheckpointCallback] Saving checkpoint at step")
                    file_path = f"{self.save_path}/{self.name_prefix}_episode_{self.episode_counter}.zip"
                    self.model.save(file_path)
                    if self.verbose > 0:
                        print(f"Checkpoint saved: {file_path}")
        return True
