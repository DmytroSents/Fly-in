"""graph.py can use Zone objects and Connection directly.
no need for <int> IDs or a separate 'links' dictionary """
from typing import Optional
from header import Map, Zone, Connection


class Graph:
    #represent zones and connections between 'em

    def __init__(self, map_data: Map) -> None:
        self.map = map_data

        # Each zone has a list of its usable connections
        self.adjacency: dict[Zone, list[Connection]] = {}

        self.connections: dict[tuple[str, str], Connection] = {}

        for zone in map_data.zones.values():
            self.adjacency[zone] = []

        for connection in map_data.connections:
            zone_a = connection.zone_a
            zone_b = connection.zone_b

            # Save the connection in both directions
            key = (zone_a.name, zone_b.name)
            key_revers = (zone_b.name, zone_a.name)

            self.connections[key] = connection
            self.connections[key_revers] = connection

            # Blocked zones cannot be used by drones
            if zone_a.is_blocked() or zone_b.is_blocked():
                continue

            self.adjacency[zone_a].append(connection)
            self.adjacency[zone_b].append(connection)

	# Get()-ters
    def nb_drones(self) -> int:
        return self.map.nb_drones

    def nb_zones(self) -> int:
        return len(self.map.zones)

    def nb_links(self) -> int:
        return len(self.map.connections)

    def start(self) -> Zone:
        #starting zone
        return self.map.start

    def goal(self) -> Zone:
        #end-zone
        return self.map.end

    def zone(self, name: str) -> Zone:
        #zone by name
        return self.map.get_zone(name)

    def is_blocked(self, zone: Zone) -> bool:
        return zone.is_blocked()

    def zone_capacity(self, zone: Zone) -> int:
        return zone.max_drones

    def link_capacity(self, connection: Connection) -> int:
        return connection.max_link_capacity

    def zone_has_place(self, zone: Zone, occupied: int) -> bool:
        if occupied < zone.max_drones:
            return True
        return False

    def link_has_place(self, connection: Connection, in_flight: int) -> bool:
        if in_flight < connection.max_link_capacity:
            return True
        return False

    def link(
        self, zone_a: Zone, zone_b: Zone
    ) -> Optional[Connection]:
        #find connection between two zones
        key = (zone_a.name, zone_b.name)
        return self.connections.get(key)

    def cost_into(self, zone: Zone) -> int:
        return zone.movement_cost()

    def edges(self, zone: Zone) -> list[Connection]:
        return self.adjacency[zone]

    def neighbors(self, zone: Zone) -> list[Zone]:
        # all usable neighboring zones
        result: list[Zone] = []

        for connection in self.edges(zone):
            result.append(connection.get_other(zone))

        return result

    def find_connection(
        self, zone_a: Zone, zone_b: Zone
    ) -> Optional[Connection]:
        #find connection (any direction)
        return self.link(zone_a, zone_b)
