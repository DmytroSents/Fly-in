from typing import NoReturn, Optional
from header import Connection, Map, Zone, ZoneType


class ParseError(Exception):
    # if malformed map_file

    def __init__(self, line: int, message: str) -> None:
        # the line number and message
        if line > 0:
            text = "line " + str(line) + ": " + message
        else:
            text = message
        super().__init__(text)


class MapParser:
    # check file line by line

    ZONE_KEYWORDS = ["start_hub", "end_hub", "hub"]
    ZONE_META_KEYS = ["zone", "color", "max_drones"]
    LINK_META_KEYS = ["max_link_capacity"]

    def __init__(self) -> None:
        # create a parser with empty fields
        self.line_no = 0
        self.nb_drones = 0          # 0 means: not defined yet
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.link_names: list[str] = []
        self.start: Optional[Zone] = None
        self.end: Optional[Zone] = None

    def parse_file(self, path: str) -> Map:
        # read the file `path` and return the Map
        try:
            with open(path, encoding="utf-8") as file:
                text = file.read()
        except (OSError, UnicodeDecodeError) as error:
            raise ParseError(
                0, "cannot read '" + path + "': " + str(error)
            ) from error
        for raw in text.splitlines():
            self.line_no += 1
            # split to remove trailing comments
            parts = raw.split("#", 1)
            content = parts[0]
            content = content.strip()
            if content == "":
                continue
            key, colon, body = content.partition(":")
            if colon == "":
                self.fail("expected '<keyword>: <value>'")
            self.parse_line(key.strip(), body.strip())
        return self.build_map()

    def fail(self, message: str) -> NoReturn:
        # if Error == stop
        raise ParseError(self.line_no, message)

    def parse_line(self, key: str, body: str) -> None:
        # checks non-empty line
        if self.nb_drones == 0:
            if key != "nb_drones":
                self.fail("first line must be 'nb_drones: <int>'")
            self.nb_drones = self.positive_int(body, "nb_drones")
        elif key == "nb_drones":
            self.fail("'nb_drones' defined more than once")
        elif key in self.ZONE_KEYWORDS:
            self.parse_zone(key, body)
        elif key == "connection":
            self.parse_connection(body)
        else:
            self.fail("unknown key'" + key + "'")

    def parse_zone(self, keyword: str, body: str) -> None:
        # check a hub-line and add to Zone
        head, meta = self.split_metadata(body, self.ZONE_META_KEYS)
        fields = head.split()
        if len(fields) != 3:
            self.fail(
                "expected '" + keyword + ": <name> <x> <y> [metadata]'"
            )
        name = fields[0]
        if "-" in name:
            self.fail("zone name '" + name + "' must not contain dashes")
        if name in self.zones:
            self.fail("duplicate zone name '" + name + "'")
        x = self.integer(fields[1], "x")
        y = self.integer(fields[2], "y")
        zone_type = self.zone_type(meta.get("zone", "normal"))

        capacity = self.positive_int(
            meta.get("max_drones", str(self.nb_drones)),
            "max_drones"
        )

        zone = Zone(name, x, y, zone_type, meta.get("color"), capacity)
        if keyword == "start_hub":
            if self.start is not None:
                self.fail("more than one start_hub defined")
            self.start = zone
        elif keyword == "end_hub":
            if self.end is not None:
                self.fail("more than one end_hub defined")
            self.end = zone
        self.zones[name] = zone

    def parse_connection(self, body: str) -> None:
        # check a connection line and add the connection
        head, meta = self.split_metadata(body, self.LINK_META_KEYS)
        usage = "expected 'connection: <zone1>-<zone2> [metadata]'"
        names = head.split("-")
        if len(head.split()) != 1 or len(names) != 2:
            self.fail(usage)
        first = names[0]
        second = names[1]
        if first == "" or second == "":
            self.fail(usage)
        if first not in self.zones:
            self.fail("connection uses undefined zone '" + first + "'")
        if second not in self.zones:
            self.fail("connection uses undefined zone '" + second + "'")
        if first == second:
            self.fail("zone '" + first + "' is linked to itself")

        link_name = first + "-" + second
        reverse_name = second + "-" + first
        if link_name in self.link_names or reverse_name in self.link_names:
            self.fail("duplicate connection '" + head + "'")
        self.link_names.append(link_name)

        capacity = self.positive_int(
            meta.get("max_link_capacity", "1"), "max_link_capacity"
        )
        connection = Connection(
            self.zones[first], self.zones[second], capacity
        )
        self.connections.append(connection)

    def build_map(self) -> Map:
        # run the checks that need and create the Map
        if self.nb_drones == 0:
            raise ParseError(0, "missing 'nb_drones' (file empty?)")
        if self.start is None:
            raise ParseError(0, "missing 'start_hub'")
        if self.end is None:
            raise ParseError(0, "missing 'end_hub'")
        return Map(self.nb_drones, self.zones, self.connections,
                   self.start, self.end)

    def split_metadata(
        self, body: str, allowed: list[str]
    ) -> tuple[str, dict[str, str]]:
        # split 'main part [k=v k=v]' into the main part and a dict
        head, bracket, tail = body.partition("[")
        if bracket == "":
            return head.strip(), {}
        if not tail.endswith("]") or "[" in tail or "]" in tail[:-1]:
            self.fail("malformed metadata, expected [key=value ...]")
        meta: dict[str, str] = {}
        for token in tail[:-1].split():
            key, equals, value = token.partition("=")
            if equals == "" or key == "" or value == "":
                self.fail("invalid metadata entry '" + token + "'")
            if key not in allowed:
                self.fail("unknown metadata key '" + key + "'")
            if key in meta:
                self.fail("duplicate metadata key '" + key + "'")
            meta[key] = value
        return head.strip(), meta

    def integer(self, text: str, what: str) -> int:
        # try convert <str> to <int>
        message = what + " must be an integer, got '" + text + "'"
        try:
            return int(text)
        except ValueError:
            self.fail(message)

    def positive_int(self, text: str, what: str) -> int:
        # like above but reject negatives
        value = self.integer(text, what)
        if value < 1:
            self.fail(what + " must be positive, got " + str(value))
        return value

    def zone_type(self, text: str) -> ZoneType:
        # turn text into a ZoneType, or reject if its invalid
        try:
            return ZoneType(text)
        except ValueError:
            self.fail("invalid zone type '" + text + "'")
