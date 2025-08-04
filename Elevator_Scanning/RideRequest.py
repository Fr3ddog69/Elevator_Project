class RideRequest:
    def __init__(self, guest):
        self.guest         = guest
        self.boarded_event = guest.env.event()
        self.arrived_event = guest.env.event()