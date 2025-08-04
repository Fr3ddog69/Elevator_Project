import simpy
import RideRequest, DestinationRequest
from ElevatorException import ElevatorFull
import copy


class Elevator:

    def __init__(
        self,
        env: simpy.Environment,
        queue: simpy.Store,
        pickup_queue,
        mutex: simpy.Resource,
        capacity: int = 5,
        door_time: float = 0.08,
        id: int = 0,
        min_floor: int = 0,
        max_floor: int = 9,
    ):
        self.env = env
        self.queue = queue
        self.capacity = capacity
        self.door_time = door_time
        self.current_floor = min_floor
        self.min_floor = min_floor
        self.max_floor = max_floor
        self.direction = 1  # 1 = up, -1 = down
        self.id = id
        self.riders = []  # guests in the elevator
        self.pickups = []  # RideRequest objects
        self.dropoffs = []  # DestinationRequest objects
        self.door = False
        self.pickup_queue = pickup_queue
        self.mutex = mutex
        # Start elevator process
        env.process(self.run_elevator())

    def run_elevator(self):
        while True:
            # --- 1) Collect requests ---
            yield from self._collect_requests()

            # --- 2) Check if we should stop at this floor ---
            if self._should_stop_here():
                yield from self._door_cycle()
                # After stop, go to start of loop
                if len(self.riders) < self.capacity:
                    continue

            # --- 3) Move to next floor ---
            yield from self._move_one_floor()

    def _collect_requests(self):
        """Non-blocking: retrieve all new requests from the queue."""
        while self.queue.items:
            req = yield self.queue.get()
            if isinstance(req, RideRequest.RideRequest):
                req.floor = req.guest.current_floor
                self.pickups.append(req)
                req_event = self.mutex.request()
                yield req_event
                self.pickup_queue.append(req)
                yield self.mutex.release(req_event)
            elif isinstance(req, DestinationRequest.DestinationRequest):
                self.dropoffs.append(req)

    def _should_stop_here(self) -> bool:
        """Returns True if the elevator should open doors at the current floor."""
        highest_target = 0
        current_floor = False
        # Drop-offs at current floor
        for req in self.dropoffs:
            if req.target_floor > highest_target:
                highest_target = req.target_floor
            if req.target_floor == self.current_floor:
                return True
        # Pick-ups at current floor in travel direction
        for req in self.pickups:
            if req.floor > highest_target:
                highest_target = req.floor
            direction = 1 if req.guest.target_floor > self.current_floor else -1
            if req.floor == self.current_floor and direction == self.direction:
                return True
            if req.floor == self.current_floor:
                current_floor = True
        if (
            current_floor
            and self.direction == 1
            and highest_target <= self.current_floor
        ):
            self.direction *= -1
            return True
        if (
            highest_target <= self.current_floor
            and self.direction != -1
            and self.current_floor != 0
        ):
            self.direction *= -1
        return False

    def _door_cycle(self):
        """Doors open, guests exit and enter, doors close."""
        # Doors open
        self.door = True
        yield self.env.timeout(self.door_time)

        # Guests exit
        for req in list(self.dropoffs):
            if req.target_floor == self.current_floor:
                self.dropoffs.remove(req)
                req.arrived_event.succeed()
                if req.guest in self.riders:
                    self.riders.remove(req.guest)

        req_event = self.mutex.request()
        print("ElevatorRequestsID " + str(self.id))
        yield req_event
        que = copy.copy(self.pickup_queue)

        print("Elevator has mutex: " + str(self.id))
        for req in que:
            direction = 1 if req.guest.target_floor > self.current_floor else -1
            if req.floor == self.current_floor and direction == self.direction:
                if (
                    len(self.riders) < self.capacity
                    and (req.guest.current_floor == self.current_floor)
                    and (
                        req.guest.state == "waiting"
                        or req.guest.state == "waiting_on_floor"
                    )
                ):
                    self.pickup_queue.remove(req)
                    self.riders.append(req.guest)
                    req.guest.elevator_id = self.id
                    print("Elevator: " + str(self.id) + "Request: " + str(req))
                    req.boarded_event.succeed()
                    if req in self.pickups:
                        self.pickups.remove(req)
                elif (
                    req.guest.state == "waiting"
                    or req.guest.state == "waiting_on_floor"
                ):
                    self.pickup_queue.remove(req)
                    if req in self.pickups:
                        self.pickups.remove(req)
                    req.boarded_event.fail(
                        ElevatorFull(f"Elevator {self.id} is full ({self.capacity})")
                    )

        # Boarding
        for req in list(self.pickups):
            direction = 1 if req.guest.target_floor > self.current_floor else -1
            if req.floor == self.current_floor and direction == self.direction:
                self.pickups.remove(req)
                if req not in self.pickup_queue:
                    continue
                elif (
                    (len(self.riders) < self.capacity)
                    and (req.guest.current_floor == self.current_floor)
                    and (
                        req.guest.state == "waiting"
                        or req.guest.state == "waiting_on_floor"
                    )
                ):
                    self.riders.append(req.guest)
                    req.guest.elevator_id = self.id
                    req.boarded_event.succeed()
                    self.pickup_queue.remove(req)
                elif (
                    req.guest.state != "waiting"
                    and req.guest.state != "waiting_on_floor"
                ):
                    self.pickup_queue.remove(req)
                else:
                    self.pickup_queue.remove(req)
                    req.boarded_event.fail(
                        ElevatorFull(f"Elevator {self.id} is full ({self.capacity})")
                    )
        self.mutex.release(req_event)

        # Doors close
        yield self.env.timeout(self.door_time)
        self.door = False

    def _move_one_floor(self):
        """Moves elevator by one floor, includes SCAN logic and direction reversal."""
        # Calculate next floor
        if len(self.pickups) == 0 and len(self.riders) == 0 and not self.door:
            if self.current_floor == 0:
                yield self.env.timeout(1)
                return
            self.direction = -1
        if not self.door:
            next_floor = self.current_floor + self.direction

            if next_floor == self.max_floor or next_floor == self.min_floor:
                self.direction *= -1
            # Travel time: exactly 1 second per floor
            if next_floor < self.min_floor:
                next_floor = self.min_floor
                self.direction == 1

            # Update current floor
            self.current_floor = next_floor
            yield self.env.timeout(4)
