from stable_baselines3.common.callbacks import BaseCallback


class StopTrainingOnEpisodes(BaseCallback):
    """
    Callback that stops training after a fixed number of episodes.
    """

    def __init__(self, n_episodes, verbose=0):
        super().__init__(verbose)
        self.n_episodes = n_episodes
        self.episodes_so_far = 0

    def _on_step(self) -> bool:
        dones = self.locals.get("dones")
        if dones is not None:
            for done in dones:
                if done:
                    self.episodes_so_far += 1
                    if self.verbose > 0:
                        print(
                            f"[Callback] Episode {self.episodes_so_far} of {self.n_episodes}"
                        )
        return self.episodes_so_far < self.n_episodes
