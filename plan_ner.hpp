#pragma once

#include "graph.hpp"

//   drone : 0++ index (printed as D<drone + 1>)
//   to = just an ID of adjacent zone
struct Move {
    int     drone;
    int     to;
};

using Turn = std::vector<Move>;        // everything decided for 1(one) turn
using Plan = std::vector<Turn>;        // plan[0] is turn 1


class Planner {	//ABC for any routing algorithm(why not)
public:
    virtual ~Planner() = default;

    // turn-by-turn movement plan
    virtual Plan solve(const Graph &graph) = 0;
};
