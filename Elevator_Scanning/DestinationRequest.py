class DestinationRequest:
    def __init__(self, target_floor, guest):
        self.target_floor  = target_floor
        self.guest         = guest
        # Event, das der Elevator beim Erreichen der Etage feuer (=succeed()) wird
        self.arrived_event = guest.env.event()