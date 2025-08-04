import simpy
import numpy as np
from ElevatorException import ElevatorFull
import RideRequest
import DestinationRequest
import Wait
import math
import random


class Guest:
    StdToleranceRequest = 5.0
    StdToleranceWorking = 50

    def __init__(
        self,
        env: simpy.RealtimeEnvironment,
        guest_id: int,
        building,
        no_floor_zero=False,
        working_time=5,
    ):
        self.env = env
        self.id = guest_id
        self.building = building

        self.state = "None"  # possible values: waiting, in_elevator, on_floor, left, waiting_on_floor
        self.current_floor = 0
        self.no_floor_zero = no_floor_zero

        if self.no_floor_zero != "False":
            # Calculate maximum number of people allowed per floor (without floor zero)
            max_val = math.ceil(building.max_guests / (building.num_floors - 1))
            # Find all possible floor indices
            all_possible_indices = []
            for i in range(1, building.num_floors):
                if building.floor_counts[i] < max_val:
                    all_possible_indices.append(i)

        else:
            # Calculate maximum number of people allowed per floor (with floor zero)
            max_val = math.ceil(building.max_guests / building.num_floors)
            # Find all possible floor indices
            all_possible_indices = []
            for i in range(building.num_floors):
                if building.floor_counts[i] < max_val:
                    all_possible_indices.append(i)

        # Randomly select a target floor from possible indices
        self.target_floor = int(np.random.choice(all_possible_indices))
        building.floor_counts[self.target_floor] += 1

        # Graphics-related indices
        self.waiting_index = len(building.riders)
        self.floor_index = None
        self.elevator_id = None
        self.remaining_time = random.randint(22800, 34700)
        # Parameters
        self.working_time = working_time  # time to spend on the floor

        # Start the guest process
        self.process = env.process(self.run())

    def call_elevator(self, waiting_state="waiting"):
        """
        Requests the elevator and waits until the guest can board.
        Returns (start_waiting, end_waiting).
        """
        start_waiting = self.env.now
        while True:
            try:
                self.state = waiting_state
                req = RideRequest.RideRequest(self)
                yield self.building.dispatcher_queue.put(req)
                yield req.boarded_event
                break
            except ElevatorFull:
                continue
        end_waiting = self.env.now
        return start_waiting, end_waiting

    def ride_elevator(self, target_floor, start_waiting, wt):
        """
        Sends the destination request and waits for arrival. Logs the ride.
        """
        self.state = "in_elevator"
        dest_req = DestinationRequest.DestinationRequest(target_floor, self)
        yield self.building.dispatcher_queue.put(dest_req)
        yield dest_req.arrived_event
        travel_time = self.env.now - (start_waiting + wt)
        self.building.log(
            time=start_waiting,
            guest_id=self.id,
            mode="elevator_drive",
            wait_time=wt,
            travel_time=travel_time,
        )
        self.current_floor = target_floor
        self.state = "on_floor"

    def work_and_maybe_move(self):
        # Guest works on the floor and may decide to change floors
        while self.remaining_time > 0:
            yield self.env.timeout(1)
            self.remaining_time -= 1

            # With small probability, guest decides to change floors (if more than 1 floor)
            if self.building.num_floors > 1 and random.random() < 0.000555:
                if self.no_floor_zero != "False":
                    # Find all possible floor indices (excluding zero)
                    all_possible_indices = []
                    for i in range(1, self.building.num_floors):
                        all_possible_indices.append(i)
                else:
                    # Find all possible floor indices (including zero)
                    all_possible_indices = []
                    for i in range(self.building.num_floors):
                        all_possible_indices.append(i)

                # Move to another floor (excluding the current one)
                all_possible_indices.remove(self.current_floor)
                self.target_floor = int(np.random.choice(all_possible_indices))
                self.building.floor_counts[self.target_floor] += 1
                self.building.floor_counts[self.current_floor] -= 1
                self.state = "waiting_on_floor"
                start_waiting, end_waiting = yield from self.call_elevator(
                    "waiting_on_floor"
                )
                wt = end_waiting - start_waiting

                self.building.log(
                    time=start_waiting,
                    guest_id=self.id,
                    mode="elevator_waiting",
                    wait_time=wt,
                    travel_time=None,
                )

                yield from self.ride_elevator(self.target_floor, start_waiting, wt)
                total_traveltime = self.env.now - start_waiting
                self.remaining_time -= total_traveltime

    def run(self):
        # Main process for a guest
        self.state = "waiting"
        if self.target_floor == 0:
            self.state = "on_floor"
        else:
            # Initial ride to the target floor
            start_waiting, end_waiting = yield from self.call_elevator("waiting")
            wt = end_waiting - start_waiting
            self.building.log(
                time=start_waiting,
                guest_id=self.id,
                mode="elevator_waiting",
                wait_time=wt,
                travel_time=None,
            )
            yield from self.ride_elevator(self.target_floor, start_waiting, wt)
            total_traveltime = self.env.now - start_waiting
            self.remaining_time -= total_traveltime

        yield from self.work_and_maybe_move()

        # Ride back to floor zero if not already there
        if self.current_floor != 0:
            self.target_floor = 0
            start_waiting, end_waiting = yield from self.call_elevator(
                "waiting_on_floor"
            )
            wt = end_waiting - start_waiting
            self.building.log(
                time=start_waiting,
                guest_id=self.id,
                mode="elevator_waiting",
                wait_time=wt,
                travel_time=None,
            )
            yield from self.ride_elevator(0, start_waiting, wt)

        self.state = "left"
        self.building.people_left_building += 1
