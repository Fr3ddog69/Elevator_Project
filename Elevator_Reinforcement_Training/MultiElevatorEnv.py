import gymnasium as gym
from gymnasium import spaces
import numpy as np
from Guest import Guest
from Elevator import Elevator
from Visualization import (
    plot_wait_times_per_hour,
    plot_travel_times_per_hour,
    plot_total_travel_times_per_hour,
    plot_guest_counts_per_hour,
    plot_average_total_time_per_hour,
)


class MultiElevatorEnv(gym.Env):

    def __init__(
        self,
        num_elevators=3,
        num_floors=10,
        max_passengers=5,
        max_guests=200,
        spawn_intervall=120 * 60,
        working_time_mean=480 * 60,
        working_time_std=50 * 60,
        sim_step_size=1,
        ride_time=4,
        door_time=4,
        episodes_so_far=0,
    ):
        super().__init__()
        self.num_elevators = num_elevators
        self.num_floors = num_floors
        self.max_passengers = max_passengers
        self.max_guests = max_guests
        self.spawn_intervall = spawn_intervall
        self.working_time_mean = working_time_mean
        self.working_time_std = working_time_std
        self.sim_step_size = sim_step_size
        self.ride_time = ride_time
        self.door_time = door_time
        self.action_space = spaces.MultiDiscrete([3] * self.num_elevators)
        self.logs = []
        self.allguests = []
        self.left_guests = []
        self.guests_in_elevator = []
        self.last_logs = None
        self.total_reward = 0
        self.episodes_so_far = episodes_so_far
        # Low/High for each elevator
        self.observation_space = self.build_obs_space(
            self.num_elevators, self.num_floors, self.max_passengers, self.max_guests
        )

        self.reset()

    def build_obs_space(self, num_elevators, num_floors, max_passengers, max_guests):
        # For each elevator:
        # - current_floor: [0, num_floors-1]
        # - num_passengers: [0, max_passengers]
        # - passengers target histogram: num_floors entries, [0, max_passengers]
        low_elevator = [0, 0] + [0] * 10
        high_elevator = [10 - 1, max_passengers] + [max_passengers] * 10

        # All elevators together:
        low = low_elevator * 3
        high = high_elevator * 3

        # For each floor: waiting guests [0, max_guests]
        low += [0] * 10
        high += [250] * 10

        obs_space = spaces.Box(low=np.array(low), high=np.array(high), dtype=np.int32)
        return obs_space

    def log(self, time, guest_id, mode, wait_time, travel_time):
        """Writes a log entry."""
        self.logs.append(
            {
                "time": time,
                "guest_id": guest_id,
                "mode": mode,  # 'elevator_waiting', 'elevator_drive' or 'stairs'
                "wait_time": wait_time,  # None if not relevant
                "travel_time": travel_time,  # None if not relevant
            }
        )

    def get_action_mask_for_elevator(self, elevator, min_floor=0, max_floor=9):
        mask = np.zeros(3, dtype=bool)
        # 0 = wait: always allowed
        mask[0] = True
        if elevator.busy_time > 0:
            return [1, 1, 1]
        if elevator.busy_time <= 0 and elevator.pending_action is not None:
            if elevator.pending_action[0] == "close":
                mask[0] = False
            elevator.pending_action = None

        if not elevator._guests_waiting_or_leaving():
            mask[0] = False

        # 1 = up: only if doors closed and not on top floor
        if not elevator.door_open and elevator.current_floor < max_floor:
            mask[1] = True

        # 2 = down: only if doors closed and not on ground floor
        if not elevator.door_open and elevator.current_floor > min_floor:
            mask[2] = True

        return mask

    def get_action_mask(self):
        # self.elevators: list of Elevator objects
        masks = []
        for elev in self.elevators:
            mask = self.get_action_mask_for_elevator(
                elev, min_floor=0, max_floor=self.num_floors - 1
            )
            masks.append(mask)
        # Result shape is (num_elevators, 3)
        return np.array(masks, dtype=bool)

    def reset(self, seed=None, options=None):
        self.elevators = []
        self._next_elevator_id = 0
        for _ in range(self.num_elevators):
            elevator = Elevator(
                self,
                id=self._next_elevator_id,
                min_floor=0,
                max_floor=self.num_floors - 1,
                capacity=5,
                door_time=4,
                ride_time=4,
                sim_step_size=1,
            )
            self._next_elevator_id += 1
            self.elevators.append(elevator)
        self.guests_in_building = 0
        self.guests_left_building = 0
        self.max_episode_steps = int(3000 / self.sim_step_size)
        self.episode_steps = 0
        if self.logs:
            self.last_logs = self.logs.copy()
        self.logs = []
        self.waiting_guests = []
        self.guests_on_floors = []
        self._next_guest_id = 0
        self.episodes_so_far += 1
        # For Poisson spawning:
        self.lam = self.max_guests / self.spawn_intervall
        self.mean_inter = 1 / self.lam
        self._time_since_last_spawn = 0.0
        self.time_until_next_arrival = np.random.exponential(self.mean_inter)
        obs = self._get_obs()
        info = {}
        self.allguests = []
        self.left_guests = []
        self.guests_in_elevator = []
        info["action_mask"] = self.get_action_mask()
        self.total_reward = 0
        return obs, info

    def _spawn_guest(self, direction="up", floor=None):
        if (self._next_guest_id) >= self.max_guests:
            return
        if floor is None:
            start_floor = 0  # in the morning, guests always start on ground floor
        else:
            start_floor = floor

        if direction == "up":
            possible_targets = [f for f in range(0, self.num_floors)]

        target_floor = np.random.choice(possible_targets)
        guest = Guest(
            self,
            guest_id=self._next_guest_id,
            start_floor=start_floor,
            target_floor=target_floor,
            current_floor=start_floor,
            waiting_since=self.episode_steps,
            entered_elevator_step=None,
        )
        self._next_guest_id += 1
        self.guests_in_building += 1
        self.allguests.append(guest)
        if target_floor == 0:
            self.guests_on_floors.append(guest)
            guest.state = "on_floor"
            guest.current_floor = 0
            return

        self.waiting_guests.append(guest)

    def step(self, actions):
        reward = 0
        self.episode_steps += 1
        for guest in self.guests_on_floors:
            guest.step(1, False)

        # === POISSON GUEST SPAWN ===
        self._time_since_last_spawn += self.sim_step_size
        while (
            (self.guests_in_building + self.guests_left_building) < self.max_guests
            and self._time_since_last_spawn >= self.time_until_next_arrival
        ):
            self._spawn_guest(direction="up")
            self._time_since_last_spawn -= self.time_until_next_arrival
            self.time_until_next_arrival = np.random.exponential(self.mean_inter)

        for i, action in enumerate(actions):
            self.elevators[i].do_action(action)

        # Finish actions + reward for dropoff
        for elev in self.elevators:
            if elev.busy_time <= 0 and elev.pending_action is not None:
                elev.execute_pending_action()
                if elev.pending_action[0] == "open":
                    leaving = elev.dropoff_guests()
                    if leaving:
                        for g in leaving:
                            waited_steps = int(
                                (self.episode_steps - g.entered_elevator_step) / 60
                            )
                            self.guests_in_elevator.remove(g)
                            h = 20 - waited_steps
                            reward += max(1, h)

        # Finish actions + reward for boarding + reward for dropoff
        for elev in self.elevators:
            if elev.busy_time <= 0 and elev.pending_action is not None:
                if elev.pending_action[0] == "open":
                    boarded_guests = elev.board_guests(
                        self.waiting_guests,
                    )
                    if boarded_guests:
                        for g in boarded_guests:
                            self.waiting_guests.remove(g)
                            self.guests_in_elevator.append(g)
                            waited_steps = int(
                                (self.episode_steps - g.waiting_since) / 60
                            )
                            h = 10 - waited_steps
                            reward += max(1, h)

        if len(self.left_guests) + len(self.guests_in_elevator) + len(
            self.guests_on_floors
        ) + len(self.waiting_guests) != len(self.allguests):
            print("Something is wrong here")
        done = (
            self.guests_left_building >= self.max_guests or self.episode_steps > 45000
        )
        truncated = False
        info = {}
        reward -= 0.1 * len(self.waiting_guests)
        reward -= 0.05 * len(self.guests_in_elevator)
        self.total_reward += reward
        info["action_mask"] = self.get_action_mask()
        if done:
            """
            plot_wait_times_per_hour(self.logs, episode=self.episodes_so_far + 1)
            plot_travel_times_per_hour(self.logs, episode=self.episodes_so_far + 1)
            plot_total_travel_times_per_hour(
                self.logs, episode=self.episodes_so_far + 1
            )
            plot_guest_counts_per_hour(self.logs, episode=self.episodes_so_far + 1)
            plot_average_total_time_per_hour(
                self.logs, episode=self.episodes_so_far + 1
            )
            """
            print("Step: ", self.episode_steps)
            print("Guests_left_building: ", self.guests_left_building)
            print("Guests_in_building: ", self.guests_in_building)
            print("Total_reward: ", self.total_reward)

        return self._get_obs(), reward, done, truncated, info

    def _get_obs(self):
        obs = []
        num_elevators = 3  # Or use self.num_elevators
        num_floors = 10  # Or use self.num_floors

        # Go through all existing elevators
        for elev in self.elevators:
            obs.append(elev.current_floor)
            obs.append(len(elev.passengers))
            passenger_dest_hist = [0] * 10
            for p in elev.passengers:
                passenger_dest_hist[p.target_floor] += 1
            obs.extend(passenger_dest_hist)

        # Fill missing elevators with zeros
        for _ in range(num_elevators - len(self.elevators)):
            obs.append(0)  # current_floor
            obs.append(0)  # len(passengers)
            obs.extend([0] * 10)  # Target histogram

        # Waiting guests per floor (all elevators)
        waiting_per_floor = [0] * 10
        for g in self.waiting_guests:
            waiting_per_floor[g.current_floor] += 1
        obs.extend(waiting_per_floor)

        return np.array(obs, dtype=np.int32)
