import sys
from parsing import MapParser, ParseError


def main() -> int:
    """Read the map, plan the flights, run the simulation, print the turns."""
    if len(sys.argv) != 2:
        sys.stderr.write("seems like a <map_file> is missing...\n")
        return 2

    # 1. Read and check the map file
    try:
        MapParser().parse_file(sys.argv[1])
    except ParseError as error:
        print("Error: " + str(error), file=sys.stderr)
        return 1
    print("success")

    # 2. Build the graph
    # TODO: game_map = MapParser().parse_file(sys.argv[1])   (keep the result)
    # TODO: graph = Graph(game_map)                          (graph.py)

    # 3. Plan the routes
    # TODO: planner = ...                                    (planner.py)
    # TODO: plan = planner.solve(graph)

    # 4. Check the plan with the simulation
    # TODO: simulation = Simulation(graph)                   (simulation.py)
    # TODO: result = simulation.run(plan)
    # TODO: if the plan breaks a rule: print the error to stderr, return 1

    # 5. Print one line per turn
    # TODO: for line in result.lines: print(line)

    # 6. Visual representation
    # TODO: Visualizer(...)                                  (visualizer.py)

    return 0


if __name__ == "__main__":
    sys.exit(main())
