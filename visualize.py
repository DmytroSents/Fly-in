import sys
import os
import subprocess

def parse_arguments():
    """Validates command-line arguments and paths before initializing Pygame."""
    binary_path = "./fly_in"
    map_file = None

    if len(sys.argv) == 2:
        map_file = sys.argv[1]
    elif len(sys.argv) >= 3:
        binary_path = sys.argv[1]
        map_file = sys.argv[2]
    else:
        print("Usage: python3 visualize.py [binary_path] <map_file>")
        sys.exit(1)

    if not os.path.exists(map_file):
        print(f"Error: Map path '{map_file}' not found.")
        sys.exit(1)

    if os.path.isdir(map_file):
        print(f"Error: '{map_file}' is a directory, not a map file. Please specify a file (e.g., ../maps/medium/01_dead_end_trap.txt).")
        sys.exit(1)

    if not os.path.exists(binary_path):
        print(f"Error: Binary '{binary_path}' not found. Please run 'make' first.")
        sys.exit(1)

    return binary_path, map_file

# Validate arguments early, before Pygame opens any windows
binary_path, map_file = parse_arguments()

import pygame

# Initialize Pygame safely
try:
    pygame.init()
except Exception as e:
    print(f"Error initializing Pygame: {e}")
    sys.exit(1)

WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Drone Navigation Visualizer")
font = pygame.font.SysFont(None, 24)

# Colors
BG_COLOR = (30, 30, 35)
ZONE_COLOR = (70, 130, 180)
START_COLOR = (46, 139, 87)
GOAL_COLOR = (205, 92, 92)
RESTRICTED_COLOR = (186, 85, 211)
LINK_COLOR = (100, 100, 100)
TEXT_COLOR = (240, 240, 240)
DRONE_COLORS = [
    (255, 105, 180), (0, 255, 255), (255, 215, 0), (50, 205, 50),
    (255, 69, 0), (138, 43, 226), (0, 191, 255), (255, 20, 147),
    (124, 252, 0), (255, 140, 0), (238, 130, 238), (0, 250, 154)
]

def load_map_and_output(binary_path, map_path):
    zones = {}
    connections = []
    start_id = None
    goal_id = None
    nb_drones = 1

    # 1. Parse Map File Safely
    try:
        with open(map_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.split('#')[0].strip()
                if not line or ':' not in line:
                    continue
                key, body = map(str.strip, line.split(':', 1))

                if "nb_drones" in key:
                    try:
                        nb_drones = int(body)
                    except ValueError:
                        pass
                elif key in ("start_hub", "end_hub", "hub"):
                    parts = body.split()
                    if len(parts) >= 3:
                        name = parts[0]
                        try:
                            x, y = int(parts[1]), int(parts[2])
                        except ValueError:
                            continue
                        z_type = "normal"
                        if "zone=restricted" in body:
                            z_type = "restricted"
                        elif key == "start_hub":
                            z_type = "start"
                            start_id = name
                        elif key == "end_hub":
                            z_type = "goal"
                            goal_id = name

                        zones[name] = {"x": x, "y": y, "type": z_type}
                elif key == "connection":
                    parts = body.split('[')[0].strip().split('-')
                    if len(parts) == 2:
                        connections.append((parts[0].strip(), parts[1].strip()))
    except Exception as e:
        print(f"Error reading map file: {e}")
        sys.exit(1)

    if not start_id and zones:
        start_id = list(zones.keys())[0]

    # 2. Run C++ binary to get simulation output
    sim_lines = []
    try:
        result = subprocess.run([binary_path, map_path], capture_output=True, text=True, check=True)
        sim_lines = result.stdout.strip().split('\n')
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else e.stdout.strip()
        print(f"C++ Simulation Error (Exit code {e.returncode}):\n{error_msg}")
        sys.exit(1)
    except Exception as e:
        print(f"Failed to execute binary '{binary_path}': {e}")
        sys.exit(1)

    # 3. Parse simulation turns robustly (carrying forward unmoved drones & locking goal state)
    drone_positions = {f"D{i+1}": start_id for i in range(nb_drones)}
    turn_snapshots = [drone_positions.copy()]

    for line in sim_lines:
        line = line.strip()
        if not line or line.startswith("Simulation Error"):
            continue

        current_turn_pos = turn_snapshots[-1].copy()
        moves = line.split()
        for move in moves:
            if '-' in move:
                parts = move.split('-')
                drone = parts[0]
                target = "-".join(parts[1:])
                current_turn_pos[drone] = target

        # Lock drones that have already reached the goal so they never vanish
        if goal_id:
            for d in current_turn_pos:
                if turn_snapshots[-1].get(d) == goal_id:
                    current_turn_pos[d] = goal_id

        turn_snapshots.append(current_turn_pos)

    return zones, connections, turn_snapshots, start_id, goal_id

# Helper for robust zone lookup (handles hyphens, underscores, case mismatches)
def get_zone_data(name, zones):
    if not name:
        return None
    if name in zones:
        return zones[name]
    alt1 = name.replace('-', '_')
    if alt1 in zones:
        return zones[alt1]
    alt2 = name.replace('_', '-')
    if alt2 in zones:
        return zones[alt2]
    for k, v in zones.items():
        if k.lower() == name.lower():
            return v
    return None

# Load data
zones, connections, turns, start_id, goal_id = load_map_and_output(binary_path, map_file)

# Normalize coordinates to fit screen nicely
if zones:
    min_x = min(z["x"] for z in zones.values())
    max_x = max(z["x"] for z in zones.values())
    min_y = min(z["y"] for z in zones.values())
    max_y = max(z["y"] for z in zones.values())

    padding = 80
    usable_w = WIDTH - 2 * padding
    usable_h = HEIGHT - 2 * padding - 60

    def scale_coord(x, y):
        sx = padding + (x - min_x) / ((max_x - min_x) or 1) * usable_w
        sy = padding + 60 + (y - min_y) / ((max_y - min_y) or 1) * usable_h
        return int(sx), int(sy)
else:
    def scale_coord(x, y):
        return x, y

current_turn_idx = 0
running = True
clock = pygame.time.Clock()

while running:
    screen.fill(BG_COLOR)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT or event.key == pygame.K_SPACE:
                if current_turn_idx < len(turns) - 1:
                    current_turn_idx += 1
            elif event.key == pygame.K_LEFT:
                if current_turn_idx > 0:
                    current_turn_idx -= 1
            elif event.key == pygame.K_ESCAPE:
                running = False

    # Draw connections (links)
    for u, v in connections:
        z1 = get_zone_data(u, zones)
        z2 = get_zone_data(v, zones)
        if z1 and z2:
            p1 = scale_coord(z1["x"], z1["y"])
            p2 = scale_coord(z2["x"], z2["y"])
            pygame.draw.line(screen, LINK_COLOR, p1, p2, 2)

    # Draw zones
    for name, data in zones.items():
        pos = scale_coord(data["x"], data["y"])
        color = ZONE_COLOR
        if data["type"] == "start":
            color = START_COLOR
        elif data["type"] == "goal":
            color = GOAL_COLOR
        elif data["type"] == "restricted":
            color = RESTRICTED_COLOR

        pygame.draw.circle(screen, color, pos, 18)
        pygame.draw.circle(screen, (255, 255, 255), pos, 18, 2)

        # Zone name label
        lbl = font.render(name, True, TEXT_COLOR)
        screen.blit(lbl, (pos[0] - lbl.get_width() // 2, pos[1] + 22))

    # Draw drones at current turn with fallback handling
    if turns and current_turn_idx < len(turns):
        current_snapshot = turns[current_turn_idx]
        zone_drone_counts = {}
        for drone, zone_name in current_snapshot.items():
            if zone_name not in zone_drone_counts:
                zone_drone_counts[zone_name] = []
            zone_drone_counts[zone_name].append(drone)

        for zone_name, drones in zone_drone_counts.items():
            z_data = get_zone_data(zone_name, zones)
            if z_data:
                base_pos = scale_coord(z_data["x"], z_data["y"])
                for i, drone in enumerate(drones):
                    offset_x = (i % 3 - 1) * 12
                    offset_y = (i // 3 - 1) * 12
                    d_pos = (base_pos[0] + offset_x, base_pos[1] + offset_y)

                    try:
                        d_idx = int(drone[1:]) - 1
                    except ValueError:
                        d_idx = 0
                    d_color = DRONE_COLORS[d_idx % len(DRONE_COLORS)]

                    pygame.draw.circle(screen, d_color, d_pos, 10)
                    pygame.draw.circle(screen, (0, 0, 0), d_pos, 10, 1)

                    d_lbl = font.render(drone, True, (0, 0, 0))
                    screen.blit(d_lbl, (d_pos[0] - d_lbl.get_width() // 2, d_pos[1] - d_lbl.get_height() // 2))

    # Draw UI instructions and turn counter
    max_t = max(0, len(turns) - 1)
    info_text = f"Turn: {current_turn_idx} / {max_t}  (Use RIGHT/LEFT Arrow keys to step)"
    info_surf = font.render(info_text, True, (255, 255, 255))
    screen.blit(info_surf, (20, 20))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()
