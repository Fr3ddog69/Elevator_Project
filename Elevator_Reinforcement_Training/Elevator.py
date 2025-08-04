class Elevator:
    def __init__(
        self,
        multielevator,
        id: int,
        min_floor: int = 0,
        max_floor: int = 9,
        capacity: int = 5,
        door_time: float = 4,
        ride_time: float = 4,
        sim_step_size: int = 1,
    ):
        self.id = id
        self.min_floor = min_floor
        self.max_floor = max_floor
        self.capacity = capacity
        self.door_time = door_time
        self.ride_time = ride_time
        self.sim_step_size = sim_step_size
        self.multielevator = multielevator
        self.current_floor = min_floor
        self.door_open = False
        self.busy_time = 0.0  # Time remaining until new action is possible
        self.pending_action = None  # To be picked up & processed by the environment
        self.passengers = []  # List of Guest objects or dicts

    def _guests_waiting_or_leaving(self):
        """
        Returns True if guests can board or leave on this floor.
        """
        # Count passengers who want to leave
        num_leaving = sum(
            1 for p in self.passengers if p.target_floor == self.current_floor
        )

        # Count guests waiting to board
        waiting_here = [
            g
            for g in self.multielevator.waiting_guests
            if g.current_floor == self.current_floor
        ]
        num_boarding_possible = max(
            0, self.capacity - (len(self.passengers) - num_leaving)
        )

        # Are there guests leaving?
        if num_leaving > 0:
            return True

        # Are there guests who can board? (Only if seats are available!)
        if waiting_here and num_boarding_possible > 0:
            return True

        return False

    def do_action(self, action):
        # 0 = wait, 1 = up, 2 = down
        if self.busy_time > 0:
            self.busy_time -= 1
            return  # No new action while "busy"

        if self.door_open:
            # Door is open: automatically close after waiting
            self.busy_time = self.door_time - 1
            self.pending_action = ("close", None)
            return

        # Door is closed and elevator is ready for a new action
        if action == 0:  # wait (elevator stays on the floor)
            # Check if there are guests to board or leave
            if self._guests_waiting_or_leaving():
                self.busy_time = self.door_time - 1
                self.pending_action = ("open", None)
            # Otherwise, really wait
            else:
                self.pending_action = ("close", None)
        elif action == 1:  # up
            if self.current_floor < self.max_floor and not self.door_open:
                self.busy_time = self.ride_time - 1
                self.pending_action = ("move", 1)
        elif action == 2:  # down
            if self.current_floor > self.min_floor and not self.door_open:
                self.busy_time = self.ride_time - 1
                self.pending_action = ("move", -1)

    def execute_pending_action(self):
        """Execute action after busy_time is over."""
        if self.pending_action is None:
            return
        typ, param = self.pending_action
        if typ == "move":
            self.current_floor += param
        elif typ == "open":
            self.door_open = True
        elif typ == "close":
            self.door_open = False

    def board_guests(self, waiting_guests):
        """
        Boards guests on the current floor.
        Returns: list of boarded guests.
        """
        boarded = []
        if self.door_open:
            free_seats = self.capacity - len(self.passengers)
            # Only allow as many to board as there are free seats
            to_board = [
                g for g in waiting_guests if g.current_floor == self.current_floor
            ][:free_seats]
            for guest in to_board:
                guest.state = "in_elevator"
                self.passengers.append(guest)
                boarded.append(guest)
                start_waiting = guest.waiting_since
                end_waiting = self.multielevator.episode_steps
                wt = end_waiting - start_waiting
                self.multielevator.log(
                    time=start_waiting,
                    guest_id=guest.id,
                    mode="elevator_waiting",
                    wait_time=wt,
                    travel_time=None,
                )
                guest.entered_elevator_step = self.multielevator.episode_steps
        return boarded

    def dropoff_guests(self):
        """
        Drops off all passengers at their target floor.
        Returns: list of guests who left the elevator.
        """
        leaving = []
        remaining = []
        for g in self.passengers:
            if g.target_floor == self.current_floor:
                g.state = "on_floor"
                g.current_floor = g.target_floor
                wt = g.entered_elevator_step - g.waiting_since
                travel_time = self.multielevator.episode_steps - g.entered_elevator_step
                self.multielevator.log(
                    g.waiting_since,
                    guest_id=g.id,
                    mode="elevator_drive",
                    wait_time=wt,
                    travel_time=travel_time,
                )
                leaving.append(g)
                if g.working_time_left > 0:
                    elevator_time = self.multielevator.episode_steps - g.waiting_since
                    g.working_time_left -= elevator_time
                    self.multielevator.guests_on_floors.append(g)
                else:
                    g.state = "left"
                    self.multielevator.guests_left_building += 1
                    self.multielevator.guests_in_building -= 1
                    g.left_building = True
                    self.multielevator.left_guests.append(g)
            else:
                remaining.append(g)
        self.passengers = remaining
        return leaving
