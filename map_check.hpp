#pragma once

#include <cstdio>
#include <string>
#include <sys/wait.h>
#include "flying.hpp"

struct CheckResult {
	bool		valid = false;
	int			line = 0;		// 0 = whole-file error / not applicable
	std::string	message;		// empty when valid
};

// Wrap a string in '...' so the shell treats it as ONE argument
// (spaces, quotes, $, ; in the path cannot break the command).
inline std::string shellQuote(const std::string &s)
{
	std::string out = "'";
	for (char c : s) {
		if (c == '\'')
			out += "'\\''";
		else
			out += c;
	}
	return out + "'";
}

// The script name is relative path, it’s resolved from current working directory, not from the binary.
// Running ./a.out from another folder will fail with "can't open file 'map_check.py'" !!!

// Runs: python3 <checker> <map_path>   and interprets the result.
inline CheckResult checkMap(const std::string &map_path,
							const std::string &checker = "map_check.py")
{
	CheckResult res;
	std::string cmd = "python3 " + shellQuote(checker) + " "
					+ shellQuote(map_path) + " 2>&1";

	FILE *pipe = popen(cmd.c_str(), "r");
	if (!pipe) {
		res.message = "cannot start python3";
		return res;
	}
	std::string output;
	char buf[512];
	while (fgets(buf, sizeof buf, pipe))
		output += buf;
	int status = pclose(pipe);
	int code = WIFEXITED(status) ? WEXITSTATUS(status) : -1;

	while (!output.empty() && (output.back() == '\n' || output.back() == '\r'))
		output.pop_back();

	if (code == 0) {
		res.valid = true;
		return res;
	}
	// Expected format: ERROR \t <line> \t <message>
	const std::string tag = "ERROR\t";
	size_t second_tab = output.find('\t', tag.size());
	if (code == 1 && output.compare(0, tag.size(), tag) == 0
		&& second_tab != std::string::npos) {
		try {
			res.line = std::stoi(output.substr(tag.size(),
											   second_tab - tag.size()));
		} catch (...) {
			res.line = 0;
		}
		res.message = output.substr(second_tab + 1);
	} else {
		res.message = "checker failed (exit code " + std::to_string(code)
					+ "): " + output;
	}
	return res;
}
