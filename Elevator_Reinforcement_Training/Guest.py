import numpy as np
import random
import math


class Guest:
    StdToleranceWorking = 50

    def __init__(
        self,
        multielevator,
        guest_id,
        start_floor,
        target_floor,
        current_floor,
        waiting_since,
        entered_elevator_step,
    ):
        self.id = guest_id
        self.waiting_since = waiting_since
        self.multielevator = multielevator
        self.start_floor = start_floor
        self.target_floor = target_floor
        self.working_time_left = random.randint(22800, 34700)
        self.current_floor = current_floor
        self.entered_elevator_step = entered_elevator_step
        self.state = "waiting"  # waiting, in_elevator, on_floor, left, waiting_on_floor
        self.current_floor = 0

        self.elevator_id = None

        self.entered_elevator_step = None
        self.left_building = False

    def reset_for_new_trip(self, direction="down"):
        """Assigns the guest a new target: return to the ground floor (0)"""
        if self.current_floor == 0:
            self.state = "left"
            self.left_building = True
            self.multielevator.guests_on_floors.remove(self)
            self.multielevator.guests_left_building += 1
            self.multielevator.guests_in_building -= 1
            self.multielevator.left_guests.append(self)
            return
        self.target_floor = 0
        self.state = "waiting_on_floor"
        self.waiting_since = self.multielevator.episode_steps
        self.entered_elevator_step = None
        self.multielevator.waiting_guests.append(self)
        self.multielevator.guests_on_floors.remove(self)

    def step(self, sim_step_size, force_return=False):
        """
        Executes a simulation step for this guest.
        sim_step_size: size of one RL step (e.g., 0.01)
        force_return: optionally forces guest to return to ground floor
        """
        # Guest is on the floor (working)
        if self.state == "on_floor":
            self.working_time_left -= sim_step_size
            # Working time over or forced return
            if self.working_time_left <= 0 or force_return:
                self.reset_for_new_trip(direction="down")
                return

            # 0.0555% chance to change floor
            if (
                not force_return
                and self.multielevator.num_floors > 1
                and random.random() < 0.000555
            ):
                possible = [
                    i
                    for i in range(self.multielevator.num_floors)
                    if i != self.current_floor
                ]
                if possible:
                    self.target_floor = int(np.random.choice(possible))
                    self.start_floor = self.current_floor
                    self.state = "waiting_on_floor"
                    self.waiting_since = self.multielevator.episode_steps
                    self.entered_elevator_step = None
                    self.multielevator.waiting_guests.append(self)
                    self.multielevator.guests_on_floors.remove(self)
