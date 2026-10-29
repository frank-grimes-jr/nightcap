#include "common/faction_standing.h"
#include <cassert>
#include <climits>
#include <iostream>

using namespace NightcapFaction;

int main()
{
	assert(Parse("").valid && Parse("").page == 1);
	assert(Parse("2 Knights of Truth").filter == "Knights of Truth");
	assert(Parse("2 Knights of Truth").page == 2);
	assert(Parse("tArGeT").target);
	assert(Parse("all").filter.empty());
	assert(!Parse("0").valid);
	assert(!Parse("99999999999999999999999999999999").valid);
	assert(!Parse(std::string(81, 'a')).valid);
	assert(!Parse("name\ncommand").valid);
	assert(Matches("Knights of Truth", "TRUTH"));
	assert(!Matches("Knights of Truth", "%"));
	assert(Escape("<c \"#000000\">A&B</c>").find("<c") == std::string::npos);
	assert(Bar(-2000, -2000, 2000) == "[--------------------]");
	assert(Bar(0, -2000, 2000) == "[==========----------]");
	assert(Bar(2000, -2000, 2000) == "[====================]");
	assert(Bar(INT_MIN, -2000, 2000) == Bar(-2000, -2000, 2000));
	assert(Bar(INT_MAX, -2000, 2000) == Bar(2000, -2000, 2000));
	assert(Bar(0, 0, 0) == "[fixed]");
	assert(Bar(0, 1, -1) == "[unavailable]");
	std::vector<Entry> entries;
	for (int i = 1; i <= 13; ++i) {
		entries.push_back({i, "Faction " + std::to_string(i), "Amiably", 200, 450, -1750, 2250});
	}
	auto first = Render(entries, Parse(""));
	assert(first.find("Page 1 of 3") != std::string::npos);
	assert(first.find("Faction 6 (") != std::string::npos);
	assert(first.find("Faction 7 (") == std::string::npos);
	assert(first.find("Standing: 450 (Amiably)") != std::string::npos);
	assert(first.find("Earned: 200; modifiers: 250") != std::string::npos);
	assert(first.find("Range: -1750 to 2250") != std::string::npos);
	assert(first.find("<c \"#FFFFFF\">") == 0);
	assert(first.substr(first.size() - 4) == "</c>");
	assert(Render(entries, Parse("3")).find("Faction 13 (") != std::string::npos);
	assert(Render(entries, Parse("4")).find("Choose a page from 1 to 3") != std::string::npos);
	assert(Render({}, Parse("")).find("No matching factions") != std::string::npos);
	for (auto &entry : entries) { entry.name = std::string(50, '&'); }
	assert(Render(entries, Parse(std::string(80, '&'))).size() < 4096);
	std::cout << "Faction parser, bars, totals, escaping and pagination passed\n";
}
