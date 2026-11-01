#pragma once

#include <map>
#include <vector>
#include <algorithm>
#include "graph.hpp"
#include "plan_ner.hpp"

// Plans the drones one after the other. Each drone takes the fastest path that
// still fits around the zones and links already reserved by the previous drones.
class GreedyPlanner : public Planner {
public:
    Plan solve(const Graph &graph) override
    {
        const int n = graph.nb_drones();
        std::vector<std::vector<int>> paths(n);   // paths[d][t] = zone of drone d at turn t
        Table zone_use;                           // {turn, zone} -> drones there
        Table link_use;                           // {turn, link} -> drones on it

        for (int d = 0; d < n; ++d) {
            paths[d] = findPath(graph, zone_use, link_use);
            if (paths[d].empty())
                return {};                        // goal not reachable in time
            reserve(graph, paths[d], zone_use, link_use);
        }

        // Turn the per-drone paths into the turn-by-turn plan.
        size_t last = 0;
        for (const auto &p : paths)
            last = std::max(last, p.size());

        Plan plan;
        for (size_t t = 1; t < last; ++t) {
            Turn turn;
            for (int d = 0; d < n; ++d) {
                if (t < paths[d].size() && paths[d][t] != paths[d][t - 1])
                    turn.push_back({d, paths[d][t]});
            }
            plan.push_back(turn);
        }
        return plan;
    }

private:
    using Table = std::map<std::pair<int, int>, int>;   // {turn, id} -> drones
    static constexpr int MAX_TURNS = 667;

    static int load(const Table &table, int turn, int id)
    {
        auto it = table.find({turn, id});
        return it == table.end() ? 0 : it->second;
    }

    // Marks the zones and links used by one path, so the next drones avoid them.
    static void reserve(const Graph &g, const std::vector<int> &path,
                        Table &zone_use, Table &link_use)
    {
        for (int t = 1; t < static_cast<int>(path.size()); ++t) {
            ++zone_use[{t, path[t]}];
            if (path[t] != path[t - 1]) {                       // a move, not a wait
                int link = *g.find_link(path[t - 1], path[t]);
                for (int k = 0; k < g.cost_into(path[t]); ++k)  // 2 turns if restricted
                    ++link_use[{t + k, link}];
            }
        }
    }

    // Fastest path start -> goal as "zone at each turn", or {} if none.
    // Every step takes exactly as many turns as it costs, so going through the
    // turns in order finds the earliest arrival (no priority queue needed).
    static std::vector<int> findPath(const Graph &g, const Table &zone_use,
                                     const Table &link_use)
    {
        const int n = g.nb_zones();
        // reached[t][z]: can a drone be in zone z at turn t?
        std::vector<std::vector<bool>> reached(MAX_TURNS + 3, std::vector<bool>(n, false));
        // from[t][z]: zone it came from (same zone = it waited)
        std::vector<std::vector<int>> from(MAX_TURNS + 3, std::vector<int>(n, -1));

        reached[0][g.start()] = true;
        for (int t = 0; t < MAX_TURNS; ++t) { // for each turn
            for (int u = 0; u < n; ++u) {
                if (!reached[t][u])
                    continue;
                if (u == g.goal())
                    return buildPath(g, from, t);

                // option 1: wait here one more turn
                if (!reached[t + 1][u] && load(zone_use, t + 1, u) < g.zone_capacity(u)) {
                    reached[t + 1][u] = true;
                    from[t + 1][u] = u;
                }

                // option 2: fly to a neighbour
                for (const Edge &e : g.edges(u)) {
                    int arrive = t + g.cost_into(e.to);
                    if (reached[arrive][e.to])
                        continue;
                    bool free = true;
                    for (int k = t + 1; k <= arrive; ++k) {
                        if (load(zone_use, k, e.to) >= g.zone_capacity(e.to)
                            || load(link_use, k, e.link) >= g.link_capacity(e.link))
                            free = false;
                    }
                    if (free) {
                        reached[arrive][e.to] = true;
                        from[arrive][e.to] = u;
                    }
                }
            }
        }
        return {};
    }

    // Walks back from (goal, t) to the start and fills path[turn] = zone.
    static std::vector<int> buildPath(const Graph &g,
                                      const std::vector<std::vector<int>> &from, int t)
    {
        std::vector<int> path(t + 1);
        int z = g.goal();
        while (t > 0) {
            int u = from[t][z];
            if (u == z) {                          // waited
                path[t] = z;
                --t;
            } else {                               // flew (1 turn, or 2 if restricted)
                int d = g.cost_into(z);
                for (int k = 0; k < d; ++k)
                    path[t - k] = z;               // a drone in flight counts as already there
                t -= d;
                z = u;
            }
        }
        path[0] = g.start();
        return path;
    }
};
