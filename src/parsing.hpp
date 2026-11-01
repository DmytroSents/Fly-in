#pragma once

#include "flying.hpp"

// map_check.py has already validated the file, so this parser trusts its input
// and only converts the text into a MapParam.
class Parsing {
public:
    MapParam parse(const std::string &path)
    {
        _map = MapParam();
        _ids.clear();

        //std::ifstream opens the file and closes it automatically when it goes out of scope.
        std::ifstream file(path);
        std::string raw;			// <- where I write
        while (std::getline(file, raw)) {
            std::string line = trim(raw.substr(0, raw.find('#'))); //strchr(s1, char '#')
            if (line.empty())
                continue;

            size_t colon = line.find(':');
            std::string key  = trim(line.substr(0, colon));
            std::string body = trim(line.substr(colon + 1));

            if (key == "nb_drones")
                _map.nb_drones = std::stoi(body);
            else if (key == "connection")
                parseConnection(body);
            else
                parseZone(key, body);            // start_hub, end_hub or hub
        }
        return _map;
    }

    typedef std::map<std::string, std::string> Meta;
    // using Meta = std::map<std::string, std::string>; since C++11 is more common

    MapParam                                _map;
    std::unordered_map<std::string, int>    _ids;        // zone name -> ID

    void parseZone(const std::string &key, const std::string &body)
    {
        std::string head;
        Meta meta; 			// here goes my std::map<std::string, std::string>
        splitMeta(body, head, meta);

        std::string name, x, y;		  // whitchcraft, I swear
        std::istringstream in(head); // copies the text of head into the stream and puts the cursor at the start.
        in >> name >> x >> y;		// true while reads succeed and false once a read fails (end of line/file)

        /*	std::string in '>>' name does three things:
         Skips whitespace (spaces, tabs, newlines) from the cursor onward.
         Reads characters until the next whitespace or the end of the text, and stores them in name.
         Leaves the cursor right after the word it read. Coz mine old 'C style'
         size_t s1 = head.find(' ');
         size_t s2 = head.find(' ', s1 + 1);
         name = head.substr(0, s1);
         x = head.substr(s1 + 1, s2 - s1 - 1);
         y = head.substr(s2 + 1);

         was broken when map had more than one space/tab between the fields */

        Zone z;
        z.ID = static_cast<int>(_map.zones.size()); //C cast (int)x. I love casting
        z.name = name;
        z.color = meta["color"];                 // "" when missing
        z.coordinate[0] = std::stoi(x);
        z.coordinate[1] = std::stoi(y);
        z.max_drones = meta.count("max_drones") ? std::stoi(meta["max_drones"]) : 1;

        if (key == "start_hub") {
            z.zone_type = ZoneType::Start;
            z.max_drones = _map.nb_drones;       // no limit on start / end
            _map.start_id = z.ID;
        } else if (key == "end_hub") {
            z.zone_type = ZoneType::Goal;
            z.max_drones = _map.nb_drones;
            _map.goal_id = z.ID;
        } else {
            const std::string &type = meta["zone"];
            if (type == "blocked")
                z.zone_type = ZoneType::Blocked;
            else if (type == "restricted")
                z.zone_type = ZoneType::Restricted;
            else if (type == "priority")
                z.zone_type = ZoneType::Priority;
            else
                z.zone_type = ZoneType::Normal;
        }

        _ids[z.name] = z.ID;
        _map.zones.push_back(z);
    }

    void parseConnection(const std::string &body)
    {
        std::string head;
        Meta meta;
        splitMeta(body, head, meta);

        size_t dash = head.find('-');
        Connection c;
        c.zones_id[0] = _ids[head.substr(0, dash)];   //before dash is one
        c.zones_id[1] = _ids[head.substr(dash + 1)]; // afre dash is another
        c.max_drones = meta.count("max_link_capacity") ? std::stoi(meta["max_link_capacity"]) : 1;
        _map.connections.push_back(c);
    }

    // "main part [k=v k=v]"  ->  head = "main part", meta = {k: v, ...}
    // static: the function doesn’t use any member data
    static void splitMeta(const std::string &body, std::string &head, Meta &meta)
    {
        size_t open = body.find('[');
        head = trim(body.substr(0, open));       // triimed all if there is no '['
        if (open == std::string::npos)
            return;

        size_t close = body.find(']');
        std::istringstream in(body.substr(open + 1, close - open - 1));
        std::string token;
        while (in >> token) {
            size_t eq = token.find('=');
            meta[token.substr(0, eq)] = token.substr(eq + 1);
        }
    }

    static std::string trim(const std::string &s)
    {
        const char *ws = " \t\r\n\f\v";
        size_t first = s.find_first_not_of(ws);
        if (first == std::string::npos)
            return "";
        return s.substr(first, s.find_last_not_of(ws) - first + 1);
    }
};
