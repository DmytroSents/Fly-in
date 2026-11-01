#pragma once

#include "flying.hpp"

 // for conviniense
// basicallu <Connection's> std::array<int, 2> zones_id;
struct Edge {
	int	to;		// neighbor zone ID
	int	link;	// index in connections
};

class Graph {
public:
	MapParam								_map;
	std::vector<std::vector<Edge>>			_adj;		// vector of connected zones
	std::map<std::pair<int, int>, int>		_links;    // {zone, zone} -> link index

	explicit Graph(const MapParam &map) : _map(map), _adj(map.zones.size())
	{
		for (int i = 0; i < static_cast<int>(_map.connections.size()); ++i) {
			int a = _map.connections[i].zones_id[0];
			int b = _map.connections[i].zones_id[1];
	// like connection but reversed: i == connection that joins zone A and zone B
			_links[{std::min(a, b), std::max(a, b)}] = i;
			if (is_blocked(a) || is_blocked(b))
				continue;					// unusable for any drones anyway
			_adj[a].push_back({b, i});	// zone [a] points to zone [b] via link i
			_adj[b].push_back({a, i}); // the same goes other way around
		}
	}

	// getters and if-checkers
	int nb_drones() const { return _map.nb_drones; }
	int nb_zones() const { return static_cast<int>(_map.zones.size()); }
	int nb_links() const { return static_cast<int>(_map.connections.size()); }
	int start() const { return _map.start_id; }
	int goal() const { return _map.goal_id; }
	const Zone &zone(int id) const { return _map.zones[id]; }
	bool is_blocked(int id) const { return zone(id).zone_type == ZoneType::Blocked; }
	int zone_capacity(int id) const { return zone(id).max_drones; }
	int link_capacity(int link) const { return _map.connections[link].max_drones; }
	const Connection &link(int id) const { return _map.connections[id]; }

	// Turns needed to move INTO zone `id` (2 if restricted, otherwise 1).
	int cost_into(int id) const
	{
		return zone(id).zone_type == ZoneType::Restricted ? 2 : 1;
	}

	// Usable edges out of a zone (blocked zones are already filtered out).
	const std::vector<Edge> &edges(int id) const { return _adj[id]; }

	// Link between two zones, if any (in either order, blocked zones included).
	std::optional<int> find_link(int a, int b) const
	{
		auto it = _links.find({std::min(a, b), std::max(a, b)});
		if (it == _links.end())
			return std::nullopt;
		return it->second;
	}
};
