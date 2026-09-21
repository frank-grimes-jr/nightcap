#pragma once
#include <cctype>
#include <string>
#include <vector>

namespace NightcapTunnel {
inline std::string FirstName(const std::string &name)
{
	auto start = name.find_first_not_of("#! ");
	if (start == std::string::npos) { return {}; }
	auto end = name.find_first_of(" _0123456789", start);
	return name.substr(start, end == std::string::npos ? end : end - start);
}

inline std::string Auction(const std::vector<std::string> &items, bool buying, unsigned variant)
{
	if (items.empty()) { return {}; }
	const char *separators[] = {" // ", " -- ", ", "};
	const char *openings[] = {"", "Anyone need these? ", "Clearing a bag: ", "Before I head out, ", "At the tunnel, "};
	const char *endings[] = {" - come hail me.", " - one of each left.", " - near the merchants.", " - stop by if interested."};
	std::string line = buying ? "WTB " : std::string(openings[(variant / 3) % 5]) + "WTS ";
	for (const auto &item : items) {
		if (&item != &items.front()) { line += separators[variant % 3]; }
		line += item;
	}
	line += buying ? " - hail me before handing anything over." : endings[(variant / 15) % 4];
	// Item links contain binary framing: omit an oversized message, never cut a link.
	return line.size() <= 400 ? line : std::string{};
}
}
