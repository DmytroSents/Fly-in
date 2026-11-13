import sys
from parsing import MapParser, ParseError
from graph import Graph
from simulating import Simulation


def main() -> int:
    if len(sys.argv) != 2:
        sys.stderr.write("seems like a <map_file> is missing...\n")
        return 2

    # Read file and build The_Map
    try:
        game_map = MapParser().parse_file(sys.argv[1])
    except ParseError as error:
        print("Error: " + str(error), file=sys.stderr)
        return 1

    # Build the Graph
    try:
        graph = Graph(game_map)
    except ValueError as error:
        print("Error: " + str(error), file=sys.stderr)
        return 1

    # Do the thing
    try:
        simulation = Simulation(game_map, graph)
        simulation.run()
    except ValueError as error:
        print("Error: " + str(error), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
