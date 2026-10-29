#pragma once

#include <algorithm>
#include <cstdint>
#include <string>
#include <vector>

namespace NightcapFaction {
constexpr size_t PageSize = 6;

struct Request {
	bool valid = true;
	bool target = false;
	size_t page = 1;
	std::string filter;
};

inline std::string Lower(std::string value)
{
	for (auto &c : value) {
		if (c >= 'A' && c <= 'Z') { c = static_cast<char>(c + ('a' - 'A')); }
	}
	return value;
}

inline std::string Trim(const std::string &value)
{
	const auto start = value.find_first_not_of(' ');
	return start == std::string::npos ? "" : value.substr(start, value.find_last_not_of(' ') - start + 1);
}

// Optional page first, then an unquoted, literal name search. Never SQL input.
inline Request Parse(const std::string &input)
{
	Request request;
	if (input.size() > 80 || std::any_of(input.begin(), input.end(), [](unsigned char c) { return c < 32 || c == 127; })) {
		request.valid = false;
		return request;
	}
	request.filter = Trim(input);
	if (Lower(request.filter) == "target") {
		request.target = true;
		request.filter.clear();
		return request;
	}
	const auto space = request.filter.find(' ');
	const auto first = request.filter.substr(0, space);
	if (!first.empty() && std::all_of(first.begin(), first.end(), [](char c) { return c >= '0' && c <= '9'; })) {
		if (first.size() > 5) { request.valid = false; return request; }
		request.page = static_cast<size_t>(std::stoul(first));
		if (request.page == 0) { request.valid = false; return request; }
		request.filter = space == std::string::npos ? "" : Trim(request.filter.substr(space + 1));
	}
	if (Lower(request.filter) == "all") { request.filter.clear(); }
	return request;
}

inline bool Matches(const std::string &name, const std::string &filter)
{
	return Lower(name).find(Lower(filter)) != std::string::npos;
}

inline std::string Escape(const std::string &value)
{
	std::string result;
	for (unsigned char c : value) {
		switch (c) {
			case '&': result += "&amp;"; break;
			case '<': result += "&lt;"; break;
			case '>': result += "&gt;"; break;
			case '"': result += "&quot;"; break;
			default: if (c >= 32 && c != 127) { result += static_cast<char>(c); } break;
		}
	}
	return result;
}

inline std::string Bar(int64_t value, int64_t minimum, int64_t maximum)
{
	if (maximum < minimum) { return "[unavailable]"; }
	if (maximum == minimum) { return "[fixed]"; }
	const auto filled = static_cast<size_t>((std::clamp(value, minimum, maximum) - minimum) * 20 / (maximum - minimum));
	return "[" + std::string(filled, '=') + std::string(20 - filled, '-') + "]";
}

struct Entry {
	int32_t id;
	std::string name;
	std::string standing;
	int32_t earned;
	int32_t total;
	int32_t minimum;
	int32_t maximum;
};

inline std::string Render(const std::vector<Entry> &entries, const Request &request)
{
	std::string text = "<c \"#FFFFFF\">Your faction standings<br>";
	const auto pages = std::max(size_t{1}, (entries.size() + PageSize - 1) / PageSize);
	if (request.page > pages) {
		return text + "Choose a page from 1 to " + std::to_string(pages) + ".</c>";
	}
	text += "Page " + std::to_string(request.page) + " of " + std::to_string(pages) + "; " + std::to_string(entries.size()) + " factions<br>";
	if (!request.filter.empty()) { text += "Search: " + Escape(request.filter) + "<br>"; }
	text += "Bars show minimum to maximum standing.<br>NPC reactions can differ. Reopen to refresh.<br><br>";
	const auto start = (request.page - 1) * PageSize;
	for (size_t i = start; i < std::min(entries.size(), start + PageSize); ++i) {
		const auto &e = entries[i];
		text += Escape(e.name.substr(0, 50)) + " (" + std::to_string(e.id) + ")<br>";
		text += "Standing: " + std::to_string(e.total) + " (" + Escape(e.standing) + ")<br>";
		text += Bar(e.total, e.minimum, e.maximum) + "<br>";
		text += "Range: " + std::to_string(e.minimum) + " to " + std::to_string(e.maximum) + "<br>";
		text += "Earned: " + std::to_string(e.earned) + "; modifiers: " + std::to_string(static_cast<int64_t>(e.total) - e.earned) + "<br><br>";
	}
	if (entries.empty()) { text += "No matching factions.<br><br>"; }
	text += "#factions [page] [name]<br>#factions target<br>";
	text += "Modifiers include base, class, race, deity, spells and items.</c>";
	return text;
}
} // namespace NightcapFaction
