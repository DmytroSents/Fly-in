#pragma once

#include <array>
#include <string>
#include <vector>
#include <fstream>
#include <iostream>
#include <optional>
#include <sstream>
#include <map>
#include <unordered_map>

enum class ZoneType {
	Start = 0, Goal = 1, Blocked = 2,
	Restricted = 3, Normal = 4, Priority = 5,
};

struct Zone {
	int 				ID;
	std::string 		name;
	std::string 		color;
	ZoneType 			zone_type;
	std::array<int, 2>  coordinate;
	std::vector<int> 	neighbor_id;
	int 				max_drones = 1;
};

struct Connection {
	int max_drones;
	std::array<int, 2> zones_id;
};

struct MapParam {
	int						nb_drones;
	std::vector<Zone> 		zones;		// all zonez.
	int						start_id = -1;
	int						goal_id = -1;
	std::vector<Connection> connections;
};
