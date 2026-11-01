"""
Exit 0: map is valid (prints nothing).
Exit 1: map is invalid, prints  ERROR<TAB><line><TAB><message>
        (line is 0 when the problem is about the whole file).
Exit 2: anisink ense"""

import re
import sys
from pathlib import Path

ZONE_KEYWORDS = ("start_hub", "end_hub", "hub")
ZONE_KEYS = ("zone", "color", "max_drones")
LINK_KEYS = ("max_link_capacity",)
ZONE_TYPES = ("normal", "blocked", "restricted", "priority")


class MapError(Exception):
    """An invalid map; `line` is 1-based, or 0 for the whole file."""

    def __init__(self, line: int, message: str) -> None:
        super().__init__(message)
        self.line = line


def check_positive(text: str, what: str, line: int) -> None:
    """Fail unless `text` is an integer >= 1."""
    if not re.fullmatch(r"-?\d+", text):
        raise MapError(line, f"{what} must be an integer, got '{text}'")
    if int(text) < 1:
        raise MapError(line, f"{what} must be positive, got {text}")


def split_meta(
    body: str, allowed: tuple[str, ...], line: int
) -> tuple[str, dict[str, str]]:
    """Split 'main part [k=v k=v]' into the main part and a dict."""
    head, bracket, tail = body.partition("[")
    if not bracket:
        return head.strip(), {}
    if not tail.endswith("]") or "[" in tail or "]" in tail[:-1]:
        raise MapError(line, "malformed metadata, expected [key=value ...]")
    meta: dict[str, str] = {}
    for token in tail[:-1].split():
        key, eq, value = token.partition("=")
        if not eq or not key or not value:
            raise MapError(line, f"invalid metadata entry '{token}'")
        if key not in allowed:
            raise MapError(line, f"unknown metadata key '{key}'")
        meta[key] = value
    return head.strip(), meta


def check_zone(key: str, body: str, line: int, zones: set[str]) -> str:
    """Validate a hub line and return the zone name."""
    head, meta = split_meta(body, ZONE_KEYS, line)
    fields = head.split()
    if len(fields) != 3:
        raise MapError(line, f"expected '{key}: <name> <x> <y> [metadata]'")
    name, x, y = fields
    if "-" in name:
        raise MapError(line, f"zone name '{name}' must not contain dashes")
    if name in zones:
        raise MapError(line, f"duplicate zone name '{name}'")
    for value, what in ((x, "x"), (y, "y")):
        if not re.fullmatch(r"-?\d+", value):
            raise MapError(line, f"{what} must be an integer, got '{value}'")
    if meta.get("zone", "normal") not in ZONE_TYPES:
        raise MapError(line, f"invalid zone type '{meta['zone']}'")
    if not re.fullmatch(r"[A-Za-z_]*", meta.get("color", "")):
        raise MapError(line, f"invalid color '{meta['color']}'")
    if "max_drones" in meta:
        check_positive(meta["max_drones"], "max_drones", line)
    return name


def check_link(body: str, line: int, zones: set[str],
               links: set[frozenset[str]]) -> None:
    """Validate a connection line and record it in `links`."""
    head, meta = split_meta(body, LINK_KEYS, line)
    names = head.split("-")
    if len(head.split()) != 1 or len(names) != 2 or not all(names):
        raise MapError(line, "expected 'connection: <zone1>-<zone2>'")
    for name in names:
        if name not in zones:
            raise MapError(line, f"connection uses undefined zone '{name}'")
    if names[0] == names[1]:
        raise MapError(line, f"zone '{names[0]}' linked to itself")
    if "max_link_capacity" in meta:
        check_positive(meta["max_link_capacity"], "max_link_capacity", line)
    if frozenset(names) in links:
        raise MapError(line, f"duplicate connection '{head}'")
    links.add(frozenset(names))


def check_map(text: str) -> None:
    """Validate the whole map text; raise MapError at the first problem."""
    zones: set[str] = set()
    links: set[frozenset[str]] = set()
    roles: set[str] = set()
    has_drones = False
    for number, raw in enumerate(text.splitlines(), start=1):
        content = raw.split("#", 1)[0].strip()
        if not content:
            continue
        key, colon, body = content.partition(":")
        key, body = key.strip(), body.strip()
        if not colon:
            raise MapError(number, "expected '<keyword>: <value>'")
        if not has_drones:
            if key != "nb_drones":
                raise MapError(number, "first line must be 'nb_drones: N'")
            check_positive(body, "nb_drones", number)
            has_drones = True
        elif key == "nb_drones":
            raise MapError(number, "'nb_drones' defined more than once")
        elif key in ZONE_KEYWORDS:
            name = check_zone(key, body, number, zones)
            if key != "hub" and key in roles:
                raise MapError(number, f"more than one {key} defined")
            roles.add(key)
            zones.add(name)
        elif key == "connection":
            check_link(body, number, zones, links)
        else:
            raise MapError(number, f"unknown keyword '{key}'")
    if not has_drones:
        raise MapError(0, "missing 'nb_drones' (file empty?)")
    for role in ("start_hub", "end_hub"):
        if role not in roles:
            raise MapError(0, f"missing '{role}'")


def main(argv: list[str]) -> int:
    """Check argv[1] and return the exit code."""
    if len(argv) != 2:
        print("usage: checker.py <map_file>", file=sys.stderr)
        return 2
    """built-in shortcut method that opens the file, reads its entire
    contents as a string, and automatically closes the file for you."""
    try:
        check_map(Path(argv[1]).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        print(f"ERROR\t0\tcannot read '{argv[1]}': {exc}")
        return 1
    except MapError as exc:
        print(f"ERROR\t{exc.line}\t{exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
