*This project has been created as part of the 42 curriculum by <dbrusent>.*

# Fly-in

## Description

Fly-in routes a fleet of drones from a start zone to an end zone through a network of connected zones, in as few simulation turns as possible.

The program reads a map file, validates it, plans every drone's route, checks the plan with a rule-enforcing simulator, and prints one line per turn. A small graphical viewer can replay the result.

## Instructions

# Requirements
- `g++` with C++20 support, and `make`
- `python3` (used by the map checker and the viewer)
- `pygame` for the viewer: `pip install pygame`

## Build

```
make          # builds ./fly_in
make re       # clean rebuild
make fclean   # remove the binary
```

### Run

Run it from the project directory, because the map checker `map_check.py` is looked up relative to the current directory.

```
./fly_in <map_file>
make run                  # runs one of the provided maps
```

**Errors** are written to stderr with exit code 1:
- an invalid map prints `ERROR<TAB><line><TAB><message>` (line 0 means the whole file)
- a plan that breaks a rule prints `Simulation Error: turn N: ...`

### Viewer

```
python3 visualize.py <map_file>                 # uses ./fly_in
python3 visualize.py <binary_path> <map_file>
```

Keys: `Right` or `Space` = next turn, `Left` = previous turn, `Esc` = quit.

### Project layout

| File | Role |
|---|---|
| `main.cpp` | Entry point: validate, parse, plan, simulate, print |
| `map_check.py`, `map_check.hpp` | Map validation (Python script called from C++) |
| `parsing.hpp` | Turns a validated map file into data structures |
| `flying.hpp` | Data types: `Zone`, `Connection`, `MapParam` |
| `graph.hpp` | Graph with adjacency lists and lookups |
| `plan_ner.hpp` | `Planner` interface, `Move`, `Turn`, `Plan` |
| `greedy_planner.hpp` | The routing algorithm |
| `simulator.hpp` | Rule checker and output formatter |
| `bfs_cost.hpp` | Single-path BFS and Dijkstra helpers, plus a simple planner used only to test purpose |
| `main.py` | Pygame viewer |

## Algorithm choices and implementation strategy

### 1. Validation and parsing

`map_check.py` checks the whole file first: first line `nb_drones`, exactly one `start_hub` and one `end_hub`, unique zone names without dashes, integer coordinates, valid zone types, positive capacities, connections only between known zones, no duplicate or self connections, and well-formed `[...]` metadata. The first problem found is reported with its line number. `parsing.hpp` then reads the file again and only converts it, because the file is already known to be valid.

### 2. Graph

`Graph` stores, for each zone, the list of zones reachable from it together with the connection used (an adjacency list). Every connection is added in both directions. Connections to blocked zones not included in adjacency list.

### 3. Planner: prioritized planning on a time-expanded graph

The drones are planned **one after the other**. Each drone gets the fastest route that still fits around what the earlier drones already reserved. This is the idea of *Cooperative A\** (Silver, 2005), without the heuristic.

- **State.** A search state is `(zone, turn)`, not just a zone, because whether a zone is free depends on the turn, and waiting is a legal move.
- **Search.** The search steps through the turns in increasing order. `reached[t][z]` says whether a drone can be in zone `z` at turn `t`. From each reachable state it tries (a) waiting one turn, and (b) flying along each connection, which lands `cost` turns later (1, or 2 for a restricted zone). Every step costs exactly as many turns as it takes, so the first turn at which the end zone is reached is the earliest possible arrival. This is Dijkstra with one bucket per turn, so no priority queue is needed.
- **Reservation tables.** Two tables count the drones in each zone and on each connection per turn. A move is allowed only if, on every turn of the flight, the destination zone is below `max_drones` and the connection is below `max_link_capacity`. After a drone is planned, its path is written into the tables for the next drones.
- **Restricted zones.** A drone in flight counts as occupying the destination and the connection on both turns, so it never has to wait on the connection.
- **Priority zones.** When two routes arrive on the same turn, the one passing through more priority zones is kept. A drone is never delayed just to reach a priority zone.
- **Path rebuild.** Each state remembers the zone it came from; walking back from the end zone gives one zone per turn. Differences between consecutive turns become the moves.

### 4. Simulator

The simulator replays the plan turn by turn and rejects it if any rule is broken: unknown drone or zone, a move along a missing connection or into a blocked zone, a drone moving twice or while in flight, a connection or zone over capacity at the end of a turn, drones left undelivered, or turns left after the last delivery. It also produces the output lines.


### Limitations

- The method is greedy: drones are planned in order, so the result is good but not guaranteed to be the best possible for the whole fleet.
- A drone that cannot reach the end zone within `MAX_TURNS` turns makes the planner return no plan, and the simulator reports the failure. (MAX is defined by me, so it just a sanity check)

## Visual representation

`visualize.py` runs the compiled program on a map and replays its output turn by turn in a Pygame window.

- Zones are drawn at their map coordinates, scaled to fit the window, with their names.
- The `color` attribute of a zone is used when Pygame knows the colour name. Unknown names fall back to a colour by type: green for start, red for end, purple for restricted, dark gray for blocked, blue otherwise.
- Connections are drawn as lines between zones.
- Each drone is a coloured circle labelled `D<ID>`. Drones sharing a zone are spread around it so they stay readable.
- The top-left counter shows the current turn, and the arrow keys step forward and back. This makes bottlenecks, waiting drones and drones in flight easy to see.

## Testing

- The simulator acts as a built-in checker: every plan is validated before anything is printed.
- `bfs_cost.hpp` contains a simple planner that sends every drone down the same shortest path.
- Extra hand-made maps cover edge cases: no path, blocked-only routes, capacity 1 bottlenecks, restricted-zone chains, and invalid files (the error messages are expected).

## Resources

- https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
- https://www.geeksforgeeks.org/dsa/dijkstras-shortest-path-algorithm-greedy-algo-7/
- D. Silver, *Cooperative Pathfinding*, AIIDE 2005: https://cdn.aaai.org/ojs/18726/18726-52-22369-1-10-20210928.pdf
- T. Standley, *Finding Optimal Solutions to Cooperative Pathfinding Problems*, AAAI 2010: https://www.cs.huji.ac.il/~jeff/aaai10/02/AAAI10-039.pdf
- w9-pathfinding documentation (HCA\* overview): https://w9-pathfinding.readthedocs.io/latest/mapf/HCAStar.html
- Breadth-first search and Dijkstra's algorithm: Cormen, Leiserson, Rivest, Stein, *Introduction to Algorithms*
- C++ reference: https://en.cppreference.com
- Pygame documentation: https://www.pygame.org/docs/

### Use of AI

An AI assistant (Claude, GoogleGemini) were used for these tasks:

- Explaining concepts and C++ syntax: file_streams, time-expanded search, `std::optional`, structured bindings.
- Reviewing the code and suggesting simplifications: simplifying data structures, simplifying `map_check.py`.
- Drafting a rewrite of the per-drone search in `greedy_planner.hpp` and a fix for `main.py`.
- And this README (obviously).
