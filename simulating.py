"""Manage drones and their movement through the map."""

from header import Map, Drone, Zone, Connection
from graph import Graph
from pathfinding import PathFinder


class Simulation:
    """Run and manage the drone simulation."""

    def __init__(self, map_data: Map, graph: Graph) -> None:
        self.map: Map = map_data
        self.graph: Graph = graph
        self.pathfinder: PathFinder = PathFinder(graph)

        self.drones: list[Drone] = []
        self.paths: dict[Drone, list[Zone]] = {}
        self.path_positions: dict[Drone, int] = {}
        self.flight_turns: dict[Drone, int] = {}

        self.turn: int = 1
        self.turn_moves: list[str] = []

        # create all drones
        self.create_drones()

    def create_drones(self) -> None:
        """Create all drones and give them a path to the end zone."""

        path = self.pathfinder.cheapest_path()

        if len(path) == 0:
            raise ValueError("no path from start to end")

        for number in range(1, self.map.nb_drones + 1):
            drone = Drone(number, self.map.start)
            self.drones.append(drone)

            self.paths[drone] = path.copy()
            self.path_positions[drone] = 0

            if drone.zone is self.map.end:
                drone.finish()

    def zone_occupancy(self) -> dict[Zone, int]:
        """Count drones occupying or reserving each zone."""

        occupancy: dict[Zone, int] = {}

        for drone in self.drones:
            if drone.finished:
                continue

            # count the destination if the drone is flying
            current = drone.zone
            if drone.in_flight and drone.destination is not None:
                current = drone.destination

            occupancy[current] = occupancy.get(current, 0) + 1

        return occupancy

    def link_occupancy(self) -> dict[Connection, int]:
        """Count drones currently using each connection."""

        occupancy: dict[Connection, int] = {}

        for drone in self.drones:
            if drone.in_flight and drone.connection is not None:
                current = drone.connection
                occupancy[current] = occupancy.get(current, 0) + 1

        return occupancy

    def can_move(self, drone: Drone, destination: Zone) -> bool:
        """Check whether a drone can move to the destination zone."""

        # check if the drone can use the connection
        connection = self.graph.link(drone.zone, destination)

        if connection is None:
            return False

        # get current occupancy
        zones = self.zone_occupancy()
        links = self.link_occupancy()

        occupied = zones.get(destination, 0)
        in_flight = links.get(connection, 0)

        # check zone capacity
        if not self.graph.zone_has_place(destination, occupied):
            return False

        # check connection capacity
        if not self.graph.link_has_place(connection, in_flight):
            return False

        return True

    def move_drone(self, drone: Drone) -> None:
        """Move a drone to its next zone if there is enough capacity."""

        if drone.in_flight or drone.finished:
            return

        path = self.paths[drone]
        position = self.path_positions[drone]

        # check if the drone has reached the end of its path
        if position >= len(path) - 1:
            if drone.zone is self.map.end:
                drone.finish()
            return

        destination = path[position + 1]

        # check if there is enough space
        if not self.can_move(drone, destination):
            return

        connection = self.graph.link(drone.zone, destination)

        if connection is None:
            return

        # start the flight
        drone.take_off(destination, connection)
        self.path_positions[drone] += 1
        self.flight_turns[drone] = self.graph.cost_into(destination)

        # record the drone movement
        self.turn_moves.append(drone.name + "-" + destination.name)

    def print_turn(self) -> None:
        """Print the movements made during the current turn."""

        all_finished = True

        for drone in self.drones:
            if not drone.finished:
                all_finished = False
                break

        # don't print an empty turn after the simulation has finished
        if len(self.turn_moves) == 0 and all_finished:
            return

        print(str(self.turn) + ": ", end="")

        for move in self.turn_moves:
            print(move, end=" ")

        print()

    def update_flights(self) -> None:
        """Advance flights and land drones when their time is finished."""

        for drone in self.drones:
            if not drone.in_flight:
                continue

            remaining = self.flight_turns[drone]
            remaining -= 1
            self.flight_turns[drone] = remaining

            # land the drone when its flight is finished
            if remaining <= 0:
                drone.land()
                del self.flight_turns[drone]

                if drone.zone is self.map.end:
                    drone.finish()

    def run_turn(self) -> None:
        """Run one turn of the simulation."""

        self.turn_moves = []

        # update drones that were already flying
        self.update_flights()

        # get all drones that are ready to move
        ready_drones: list[Drone] = []

        for drone in self.drones:
            if not drone.in_flight and not drone.finished:
                ready_drones.append(drone)

        # prepare the movements for this turn
        planned_moves: list[tuple[Drone, Zone, Connection]] = []

        # copy current occupancy
        zones = self.zone_occupancy()
        links = self.link_occupancy()

        for drone in ready_drones:
            path = self.paths[drone]
            position = self.path_positions[drone]

            if position >= len(path) - 1:
                continue

            destination = path[position + 1]
            connection = self.graph.link(drone.zone, destination)

            if connection is None:
                continue

            occupied = zones.get(destination, 0)
            in_flight = links.get(connection, 0)

            # check zone capacity
            if not self.graph.zone_has_place(destination, occupied):
                continue

            # check connection capacity
            if not self.graph.link_has_place(connection, in_flight):
                continue

            # free the current zone
            current_occupied = zones.get(drone.zone, 0)
            zones[drone.zone] = current_occupied - 1

            # reserve the destination and connection
            zones[destination] = occupied + 1
            links[connection] = in_flight + 1

            planned_moves.append((drone, destination, connection))

        # execute all approved movements
        for drone, destination, connection in planned_moves:
            drone.take_off(destination, connection)

            self.path_positions[drone] += 1
            self.flight_turns[drone] = self.graph.cost_into(destination)

            self.turn_moves.append(
                drone.name + "-" + destination.name
            )

        # print the movements made during this turn
        self.print_turn()

        self.turn += 1

    def run(self) -> None:
        """Run the simulation until all drones reach the end."""

        while True:
            all_finished = True

            for drone in self.drones:
                if not drone.finished:
                    all_finished = False
                    break

            if all_finished:
                break

            self.run_turn()
