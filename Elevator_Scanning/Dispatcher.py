import simpy
import random
import RideRequest, DestinationRequest


class Dispatcher:

    def __init__(
        self,
        env: simpy.Environment,
        dispatcher_queue: simpy.Store,
        elevator_queues: list,
    ):
        """
        :param env: SimPy environment
        :param dispatcher_queue: Store where Guests place their requests
        :param elevator_queues: List of Stores, one per elevator
        """
        self.env = env
        self.dispatcher_queue = dispatcher_queue
        self.elevator_queues = elevator_queues
        # Elevator instances are ideally managed externally
        # Here we only need their queues
        self.num_elevators = len(elevator_queues)

    def run(self):
        """Main process of the dispatcher."""
        while True:
            req = yield self.dispatcher_queue.get()  # next request

            # 1) First elevator call
            if isinstance(req, RideRequest.RideRequest):
                # Choose a random elevator
                eid = random.randrange(self.num_elevators)
                # Remember which elevator the guest will use
                req.guest.elevator_id = eid
                # Put the request in the corresponding elevator queue
                yield self.elevator_queues[eid].put(req)

            # 2) Destination floor notification
            elif isinstance(req, DestinationRequest.DestinationRequest):
                # We assume the guest has already set req.guest.elevator_id
                eid = req.guest.elevator_id
                # Optionally check if eid is valid
                if 0 <= eid < self.num_elevators:
                    yield self.elevator_queues[eid].put(req)

            else:
                # Unknown request type
                print(f"{self.env.now}: Dispatcher received unknown request {req}")
                continue
