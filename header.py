"""Basically like a header file with
Classes that describe: zones, connections, map, drones."""

from enum import Enum
from typing import Optional


class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:
    def __init__(self, name: str, x: int, y: int,
        zone_type: ZoneType = ZoneType.NORMAL,
        color: Optional[str] = None, max_drones: int = 1,
    ) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.color = color
        self.max_drones = max_drones

    def is_blocked(self) -> bool:
        #simple comparison, that returns True (if it's true)
        return self.zone_type == ZoneType.BLOCKED

    def movement_cost(self) -> int:
        if self.zone_type == ZoneType.RESTRICTED:
            return 2
        return 1


class Connection:
    #connection goes two-ways

    def __init__(
        self, zone_a: Zone, zone_b: Zone, max_link_capacity: int = 1
    ) -> None:
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity

    def get_name(self) -> str:
        return self.zone_a.name + "-" + self.zone_b.name

    def get_other(self, zone: Zone) -> Zone:
        if zone is self.zone_a:
            return self.zone_b
        if zone is self.zone_b:
            return self.zone_a
        raise ValueError(zone.name + " is not part of " + self.get_name())


class Map:
    # The_Map itself - drones, zones, connections, start and end

    def __init__(self, nb_drones: int, zones: dict[str, Zone],
        connections: list[Connection], start: Zone, end: Zone,
    ) -> None:
        self.nb_drones = nb_drones
        self.zones = zones
        self.connections = connections
        self.start = start
        self.end = end

    def get_zone(self, name: str) -> Zone:
        return self.zones[name]


class Drone:
    #used in simulation and for printing stuff

    def __init__(self, number: int, start: Zone) -> None:
        self.number = number
        self.name = "D" + str(number)
        self.zone = start
        self.in_flight = False
        self.destination: Optional[Zone] = None
        self.connection: Optional[Connection] = None
        self.finished = False

    def take_off(self, destination: Zone, connection: Connection) -> None:
        #start a 2-turn flight toward a restricted zone
        self.in_flight = True
        self.destination = destination
        self.connection = connection

    def land(self) -> None:
        #finish flight and move the drone to its destination
        if not self.in_flight or self.destination is None:
            raise ValueError("drone is not in flight")

        self.zone = self.destination
        self.in_flight = False
        self.destination = None
        self.connection = None

    def finish(self) -> None:
       #when drone reached the end zone
        self.finished = True
