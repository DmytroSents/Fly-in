#include <iostream>
#include "flying.hpp"
#include "map_check.hpp"
#include "graph.hpp"
#include "plan_ner.hpp"
#include "greedy_planner.hpp"
#include "bfs_cost.hpp"
#include "simulator.hpp"
#include "parsing.hpp"

int main(int argc, char **argv)
{
    if (argc != 2) {
        std::cerr << "usage: " << argv[0] << " <map_file>\n";
        return 2;
    }

    // Validate the map file using the Python bridge
    CheckResult r = checkMap(argv[1]);
    if (!r.valid) {
        std::cerr << "ERROR\t" << r.line << "\t" << r.message << "\n";
        return 1;
    }
    MapParam map_param;
    try {
        Parsing parser;
        map_param = parser.parse(argv[1]);
    } catch (const std::exception &e) {
        std::cerr << "Error parsing map: " << e.what() << "\n";
        return 1;
    }

    // Plan, then check the plan with the simulator
    Graph graph(map_param);

    Routing planner;
    //GreedyPlanner planner;

    Plan plan = planner.solve(graph);
    Simulator simulator(graph);
    SimResult sim_res = simulator.run(plan);

    if (!sim_res.ok) {
        std::cerr << "Simulation Error: " << sim_res.error << "\n";
        return 1;
    }

    for (const std::string &line : sim_res.lines)
        std::cout << line << "\n";

    return 0;
}
