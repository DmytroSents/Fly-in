#pragma once

#include "plan_ner.hpp"

struct SimResult {
	bool						ok = false;
	std::string					error;			// empty when ok
	std::vector<std::string>	lines;			// one line per turn, subject's format
};

class Simulator {
public:
	explicit Simulator(const Graph &graph) : _g(graph) {}

	SimResult run(const Plan &plan) const
	{
		SimResult res;
		const int n = _g.nb_drones();

		std::vector<Status>	status(n, Status::AtZone);
		std::vector<int>	pos(n, _g.start());
		std::vector<int>	dest(n, -1);		// only meaningful while InTransit
		std::vector<int>	link_of(n, -1);
		std::vector<int>	occupancy(_g.nb_zones(), 0);
		occupancy[_g.start()] = n;
		int		delivered = 0;

		for (std::size_t t = 0; t < plan.size(); ++t) {
			const int turn = static_cast<int>(t) + 1;
			std::vector<int>	link_use(_g.nb_links(), 0);
			std::vector<bool>	busy(n, false);		// already acted this turn
			std::vector<std::pair<int, std::string>> events;	// {drone, text}

			auto fail = [&](const std::string &why) {
				res.ok = false;
				res.error = "turn " + std::to_string(turn) + ": " + why;
				return res;
			};
			auto name = [&](int d) { return "D" + std::to_string(d + 1); };
			auto arrive = [&](int d, int z) {
				pos[d] = z;
				if (z == _g.goal()) {
					status[d] = Status::Delivered;
					++delivered;
				} else {
					status[d] = Status::AtZone;
					++occupancy[z];
				}
				events.emplace_back(d, name(d) + "-" + _g.zone(z).name);
			};

			//flights started last turn land now
			for (int d = 0; d < n; ++d) {
				if (status[d] != Status::InTransit)
					continue;
				busy[d] = true;
				++link_use[link_of[d]];
				arrive(d, dest[d]);
			}

			//this turn's decisions
			for (const Move &m : plan[t]) {
				const int d = m.drone;
				if (d < 0 || d >= n)
					return fail("unknown drone index " + std::to_string(d));
				if (m.to < 0 || m.to >= _g.nb_zones())
					return fail(name(d) + ": unknown zone index " + std::to_string(m.to));
				if (busy[d])
					return fail(name(d) + " acts twice, or is in flight and cannot be moved");
				if (status[d] == Status::Delivered)
					return fail(name(d) + " is already delivered");

				const int from = pos[d];
				const std::string &from_name = _g.zone(from).name;
				const std::string &to_name = _g.zone(m.to).name;
				auto link = _g.find_link(from, m.to);
				if (!link)
					return fail(name(d) + ": '" + from_name + "' and '" + to_name + "' are not connected");
				if (_g.is_blocked(m.to))
					return fail(name(d) + " cannot enter blocked zone '" + to_name + "'");

				busy[d] = true;
				--occupancy[from];
				++link_use[*link];
				if (_g.cost_into(m.to) > 1) {						// 2-turn flight
					status[d] = Status::InTransit;
					dest[d] = m.to;
					link_of[d] = *link;
					events.emplace_back(d, name(d) + "-" + from_name + "-" + to_name);
				} else {
					arrive(d, m.to);
				}
			}

			//capacities based on the state at the end of turn
			for (int l = 0; l < _g.nb_links(); ++l) {
				if (link_use[l] > _g.link_capacity(l)) {
					const Connection &c = _g.link(l);
					return fail("link " + _g.zone(c.zones_id[0]).name + "-" + _g.zone(c.zones_id[1]).name
						+ " carries " + std::to_string(link_use[l]) + " drones (max "
						+ std::to_string(_g.link_capacity(l)) + ")");
				}
			}
			for (int z = 0; z < _g.nb_zones(); ++z) {
				if (z == _g.start() || z == _g.goal())
					continue;
				if (occupancy[z] > _g.zone_capacity(z))
					return fail("zone '" + _g.zone(z).name + "' holds " + std::to_string(occupancy[z])
						+ " drones (max " + std::to_string(_g.zone_capacity(z)) + ")");
			}

			// this turn
			std::sort(events.begin(), events.end());
			std::string line;
			for (const auto &[d, text] : events)
				line += (line.empty() ? "" : " ") + text;
			res.lines.push_back(line);

			if (delivered == n) {
				if (turn != static_cast<int>(plan.size()))
					return fail("plan goes on after all drones are delivered");
				res.ok = true;
				return res;
			}
		}
		res.error = "plan ends with " + std::to_string(delivered) + " of "
			+ std::to_string(n) + " drones delivered";
		return res;
	}

	enum class Status { AtZone, InTransit, Delivered };
	const Graph &_g;
};
