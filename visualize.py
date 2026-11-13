"""Visualize drone movements through the map using Pygame."""

import sys
import os
import subprocess

import pygame


WIDTH = 1000
HEIGHT = 800

BG_COLOR = (30, 30, 35)
ZONE_COLOR = (70, 130, 180)
START_COLOR = (46, 139, 87)
GOAL_COLOR = (205, 92, 92)
RESTRICTED_COLOR = (186, 85, 211)
PRIORITY_COLOR = (255, 215, 0)
BLOCKED_COLOR = (100, 100, 100)
LINK_COLOR = (100, 100, 100)
TEXT_COLOR = (240, 240, 240)

DRONE_COLORS = [
    (255, 105, 180), (0, 255, 255), (255, 215, 0),
    (50, 205, 50), (255, 69, 0), (138, 43, 226),
    (0, 191, 255), (255, 20, 147), (124, 252, 0),
    (255, 140, 0), (238, 130, 238), (0, 250, 154)
]


def parse_arguments() -> str:
    """Validate the map file argument."""

    if len(sys.argv) != 2:
        print("Usage: uv run python visualize.py <map_file>")
        sys.exit(1)

    map_file = sys.argv[1]

    if not os.path.exists(map_file):
        print("Error: Map file '" + map_file + "' not found.")
        sys.exit(1)

    if os.path.isdir(map_file):
        print("Error: '" + map_file + "' is a directory.")
        sys.exit(1)

    return map_file


def load_map_and_output(map_path: str) -> tuple[
    dict[str, dict[str, object]],
    list[tuple[str, str]],
    list[dict[str, str]],
    str,
    str
]:
    """Read the map and run the Python simulation."""

    zones: dict[str, dict[str, object]] = {}
    connections: list[tuple[str, str]] = []
    start_id = ""
    goal_id = ""
    nb_drones = 1

    # read the map file
    try:
        with open(map_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.split("#")[0].strip()

                if not line or ":" not in line:
                    continue

                key, body = line.split(":", 1)
                key = key.strip()
                body = body.strip()

                if key == "nb_drones":
                    nb_drones = int(body)

                elif key in ("start_hub", "end_hub", "hub"):
                    parts = body.split()

                    if len(parts) < 3:
                        continue

                    name = parts[0]

                    try:
                        x = int(parts[1])
                        y = int(parts[2])
                    except ValueError:
                        continue

                    zone_type = "normal"
                    zone_color = None

                    if key == "start_hub":
                        zone_type = "start"
                        start_id = name
                    elif key == "end_hub":
                        zone_type = "goal"
                        goal_id = name

                    # read zone metadata
                    for part in parts[3:]:
                        if part.startswith("["):
                            part = part[1:]
                        if part.endswith("]"):
                            part = part[:-1]

                        if part.startswith("zone="):
                            if zone_type not in ("start", "goal"):
                                zone_type = part.split("=", 1)[1]

                        elif part.startswith("color="):
                            zone_color = part.split("=", 1)[1]

                    zones[name] = {
                        "x": x,
                        "y": y,
                        "type": zone_type,
                        "color": zone_color
                    }

                elif key == "connection":
                    connection = body.split("[")[0].strip()
                    parts = connection.split("-", 1)

                    if len(parts) == 2:
                        connections.append(
                            (parts[0].strip(), parts[1].strip())
                        )

    except (OSError, ValueError) as error:
        print("Error reading map file: " + str(error))
        sys.exit(1)

    if not start_id and zones:
        start_id = next(iter(zones))

    if not start_id or not goal_id:
        print("Error: Map must have a start_hub and an end_hub.")
        sys.exit(1)

    # run the Python simulation
    script_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "fly-in.py"
    )

    try:
        result = subprocess.run(
            [sys.executable, script_path, map_path],
            capture_output=True,
            text=True,
            check=True
        )

    except subprocess.CalledProcessError as error:
        error_msg = error.stderr.strip()
        print("Simulation Error:")
        print(error_msg)
        sys.exit(1)

    except OSError as error:
        print("Failed to execute simulation: " + str(error))
        sys.exit(1)

    # create the initial drone positions
    drone_positions: dict[str, str] = {}

    for number in range(1, nb_drones + 1):
        drone_positions["D" + str(number)] = start_id

    turn_snapshots: list[dict[str, str]] = [
        drone_positions.copy()
    ]

    # read the movements printed by the simulation
    for line in result.stdout.splitlines():
        line = line.strip()

        if not line or ":" not in line:
            continue

        turn_number, moves_text = line.split(":", 1)

        try:
            int(turn_number.strip())
        except ValueError:
            continue

        current_positions = turn_snapshots[-1].copy()

        moves = moves_text.split()

        for move in moves:
            if "-" not in move:
                continue

            drone, target = move.split("-", 1)

            if drone in current_positions:
                current_positions[drone] = target

        turn_snapshots.append(current_positions)

    return (
        zones,
        connections,
        turn_snapshots,
        start_id,
        goal_id
    )


def get_zone_data(
    name: str,
    zones: dict[str, dict[str, object]]
) -> dict[str, object] | None:
    """Find a zone by name."""

    if name in zones:
        return zones[name]

    for zone_name, data in zones.items():
        if zone_name.lower() == name.lower():
            return data

    return None


def get_zone_color(data: dict[str, object]) -> tuple[int, int, int]:
    """Return the display color for a zone."""

    zone_type = data["type"]

    if zone_type == "start":
        return START_COLOR

    if zone_type == "goal":
        return GOAL_COLOR

    if zone_type == "restricted":
        return RESTRICTED_COLOR

    if zone_type == "priority":
        return PRIORITY_COLOR

    if zone_type == "blocked":
        return BLOCKED_COLOR

    color_name = data["color"]

    if isinstance(color_name, str):
        try:
            return pygame.Color(color_name)
        except ValueError:
            pass

    return ZONE_COLOR


def main() -> None:
    """Load the simulation and display the drone movements."""

    map_file = parse_arguments()

    zones, connections, turns, start_id, goal_id = (
        load_map_and_output(map_file)
    )

    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Drone Navigation Visualizer")

    font = pygame.font.SysFont(None, 24)
    clock = pygame.time.Clock()

    # normalize coordinates to fit the screen
    min_x = min(data["x"] for data in zones.values())
    max_x = max(data["x"] for data in zones.values())
    min_y = min(data["y"] for data in zones.values())
    max_y = max(data["y"] for data in zones.values())

    padding = 80
    usable_w = WIDTH - 2 * padding
    usable_h = HEIGHT - 2 * padding - 60

    def scale_coord(x: int, y: int) -> tuple[int, int]:
        sx = padding + (
            (x - min_x) / ((max_x - min_x) or 1)
        ) * usable_w

        sy = padding + 60 + (
            (y - min_y) / ((max_y - min_y) or 1)
        ) * usable_h

        return int(sx), int(sy)

    current_turn_idx = 0
    running = True

    while running:
        screen.fill(BG_COLOR)

        # handle keyboard events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RIGHT, pygame.K_SPACE):
                    if current_turn_idx < len(turns) - 1:
                        current_turn_idx += 1

                elif event.key == pygame.K_LEFT:
                    if current_turn_idx > 0:
                        current_turn_idx -= 1

                elif event.key == pygame.K_ESCAPE:
                    running = False

        # draw connections
        for zone_a, zone_b in connections:
            data_a = get_zone_data(zone_a, zones)
            data_b = get_zone_data(zone_b, zones)

            if data_a is not None and data_b is not None:
                pos_a = scale_coord(
                    int(data_a["x"]),
                    int(data_a["y"])
                )
                pos_b = scale_coord(
                    int(data_b["x"]),
                    int(data_b["y"])
                )

                pygame.draw.line(
                    screen, LINK_COLOR, pos_a, pos_b, 2
                )

        # draw zones
        for name, data in zones.items():
            pos = scale_coord(
                int(data["x"]),
                int(data["y"])
            )

            color = get_zone_color(data)

            pygame.draw.circle(screen, color, pos, 18)
            pygame.draw.circle(
                screen, (255, 255, 255), pos, 18, 2
            )

            label = font.render(name, True, TEXT_COLOR)

            screen.blit(
                label,
                (
                    pos[0] - label.get_width() // 2,
                    pos[1] + 22
                )
            )

        # draw drones at the current turn
        if turns and current_turn_idx < len(turns):
            current_snapshot = turns[current_turn_idx]
            zone_drone_counts: dict[str, list[str]] = {}

            for drone, zone_name in current_snapshot.items():
                if zone_name not in zone_drone_counts:
                    zone_drone_counts[zone_name] = []

                zone_drone_counts[zone_name].append(drone)

            for zone_name, drones in zone_drone_counts.items():
                data = get_zone_data(zone_name, zones)

                if data is None:
                    continue

                base_pos = scale_coord(
                    int(data["x"]),
                    int(data["y"])
                )

                for i, drone in enumerate(drones):
                    offset_x = (i % 3 - 1) * 12
                    offset_y = (i // 3 - 1) * 12

                    drone_pos = (
                        base_pos[0] + offset_x,
                        base_pos[1] + offset_y
                    )

                    try:
                        drone_index = int(drone[1:]) - 1
                    except ValueError:
                        drone_index = 0

                    color = DRONE_COLORS[
                        drone_index % len(DRONE_COLORS)
                    ]

                    pygame.draw.circle(
                        screen, color, drone_pos, 10
                    )
                    pygame.draw.circle(
                        screen, (0, 0, 0), drone_pos, 10, 1
                    )

                    label = font.render(
                        drone, True, (0, 0, 0)
                    )

                    screen.blit(
                        label,
                        (
                            drone_pos[0] - label.get_width() // 2,
                            drone_pos[1] - label.get_height() // 2
                        )
                    )

        # draw turn counter and instructions
        max_turn = max(0, len(turns) - 1)

        info_text = (
            "Turn: " + str(current_turn_idx)
            + " / " + str(max_turn)
            + "  (RIGHT/SPACE: next, LEFT: previous, ESC: quit)"
        )

        info_surface = font.render(
            info_text, True, (255, 255, 255)
        )

        screen.blit(info_surface, (20, 20))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
