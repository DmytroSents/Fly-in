"""Manage drones and their movement through the map."""

from header import Map, Drone, Zone, Connection
from graph import Graph
from pathfinding import PathFinder


class Simulation:
    """Run and manage the drone simulation."""

    def __init__(self, map_data: Map, graph: Graph) -> None:
        self.map = map_data
        self.graph = graph
        self.pathfinder = PathFinder(graph)

        self.drones: list[Drone] = []

        # create all drones
        self.create_drones()

    def create_drones(self) -> None:
        # create all drones at the start zone
        for number in range(1, self.map.nb_drones + 1):
            drone = Drone(number, self.map.start)
            self.drones.append(drone)

    def zone_occupancy(self) -> dict[Zone, int]:
        # count how many drones are in each zone
        occupancy: dict[Zone, int] = {}

        for drone in self.drones:
            if not drone.in_flight and not drone.finished:
                current = drone.zone
                occupancy[current] = occupancy.get(current, 0) + 1
        return occupancy

    def link_occupancy(self) -> dict[Connection, int]:
        # count how many drones are using each connection
        occupancy: dict[Connection, int] = {}

        for drone in self.drones:
            if drone.in_flight and drone.connection is not None:
                current = drone.connection
                occupancy[current] = occupancy.get(current, 0) + 1
        return occupancy

    def can_move(
        self, drone: Drone, destination: Zone
    ) -> bool:
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
