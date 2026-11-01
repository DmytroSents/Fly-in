#pragma once

#include <queue>
#include <functional>
#include <algorithm>
#include <vector>
#include "graph.hpp"
#include "plan_ner.hpp"

inline std::vector<int> rebuildPath(const Graph &g, const std::vector<int> &from);

// just BFS, exactly like maze.
inline std::vector<int> bfsPath(const Graph &g)
{
	std::vector<bool>	visited(g.nb_zones(), false); // (size, memset(value)) -constructor
	std::vector<int>	from(g.nb_zones(), -1);      // like my direction array
	std::queue<int>		queue;

	visited[g.start()] = true;
	queue.push(g.start());
	while (!queue.empty()) {
		int curr = queue.front();
		queue.pop();
		if (curr == g.goal())
			break;
		for (const Edge &e : g.edges(curr)) {           // like my 4 direction checks
			if (visited[e.to])
				continue;
			visited[e.to] = true;
			from[e.to] = curr;
			queue.push(e.to);
		}
	}
	if (!visited[g.goal()])
		return {};                                   // no path
	return rebuildPath(g, from);
}

// Dijkstra, I guess. almost same, but restricted zone costs 2, so it
// always expand the zone with the smallest total cost
inline std::vector<int> cheapestPath(const Graph &g)
{
	const int ALOT = 666777;
	std::vector<int>	dist(g.nb_zones(), ALOT);     // best cost found for now
	std::vector<int>	from(g.nb_zones(), -1);
	typedef std::pair<int, int> Item;                // {cost now, zone}

	//By default, std::priority_queue uses std::less, which puts the largest item on top
	// (a max-heap):so I need to swap it.	  priority_queue<T, Container, Compare> pq;
	std::priority_queue<Item, std::vector<Item>, std::greater<Item>> queue;

	dist[g.start()] = 0;
	queue.push({0, g.start()}); // {Initializer_List} syntax
	while (!queue.empty()) {
		auto item = queue.top();	 // The Pair
		int cost = item.first;      // the first number in pair
		int curr    = item.second;    // the second number in pair
		queue.pop();
		if (cost > dist[curr])
			continue;     // if outdated entry : skip it. Like 'visited' but also cost compared
		if (curr == g.goal())
			break;
		for (const Edge &e : g.edges(curr)) {
			int new_cost = cost + g.cost_into(e.to); // 1 defolt, or 2 if restricted
			if (new_cost < dist[e.to]) {
				dist[e.to] = new_cost;
				from[e.to] = curr;
				queue.push({new_cost, e.to});
			}
		}
	}
	if (dist[g.goal()] == ALOT)
		return {};                           // no path fallback, ehh
	return rebuildPath(g, from);
}

// walks back through `from` (the zone it came from) and returns the path
// start -> goal as a list of zone IDs.
inline std::vector<int> rebuildPath(const Graph &g, const std::vector<int> &from)
{
	std::vector<int> path;
	for (int z = g.goal(); z != -1; z = from[z])     // stop on [start], coz start == -1
		path.push_back(z);
	std::reverse(path.begin(), path.end());
	return path;
}

class Routing {
public:
	// gap: turns between two drone starts. -1 = automatic, 0 = all leave together
	Plan solve(const Graph &g, int gap = -1)
	{
		Plan plan;
		std::vector<int> path = cheapestPath(g);
		if (path.empty())
			return plan;
		if (gap < 0) {                                  // to avoid collision for one-by-one pass
			gap = 1;
			for (size_t k = 1; k < path.size(); ++k)
				gap = std::max(gap, g.cost_into(path[k]));
		}
		for (int d = 0; d < g.nb_drones(); ++d) {
			int arrived = d * gap;                      // turn when drone stands in path[k-1]
			for (size_t k = 1; k < path.size(); ++k) {
				int depart = arrived + 1;               // turn this move is ordered
				arrived += g.cost_into(path[k]);        // turn it lands (+2 if restricted)
				if (plan.size() < static_cast<size_t>(arrived))
					plan.resize(arrived);
				plan[depart - 1].push_back({d, path[k]});
			}
		}
		return plan;
	}
};
