#pragma once

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

// Shared presentation contract. Neither a row nor its capability bits authorize
// a transfer: the zone must recheck the current physical corpse and inventory.
namespace NightcapLoot {
constexpr std::size_t PageSize = 8;
constexpr std::size_t MaxMessage = 512;
constexpr uint32_t MaxResults = 1000000;
enum class View : uint32_t { Drops, Filters };
enum class Filter : uint32_t { Ask, AlwaysTake, Never, AlwaysNeed, AlwaysGreed };
enum class Phase : uint32_t { Personal, Shared, Rolling, Awarded, FreeGrab, FilterRecord };
enum class Action : uint32_t { Take, Leave, Need, Greed, Pass, Roll, FreeGrab, Inspect, Assign, FindCorpse, TakeNoTrade, EditFilter };
constexpr uint32_t Capability(Action action) { return uint32_t{1} << static_cast<uint32_t>(action); }
constexpr uint32_t AllCapabilities = (Capability(Action::EditFilter) << 1) - 1;
enum Setting : uint32_t { Enabled = 1, ApplyFilters = 2, AutoShow = 4, AutoTakeAll = 8, AutoSplitCoin = 16, ShowNewOnly = 32 };
constexpr uint32_t AllSettings = 63;

inline bool Number(std::string_view text, uint32_t &value)
{
	if (text.empty() || text.size() > 10) { return false; }
	uint32_t parsed = 0;
	for (const char c : text) {
		if (c < '0' || c > '9' || parsed > (UINT32_MAX - static_cast<uint32_t>(c - '0')) / 10) { return false; }
		parsed = parsed * 10 + static_cast<uint32_t>(c - '0');
	}
	value = parsed;
	return true;
}

inline std::string Hex(std::string_view text)
{
	std::string output;
	for (unsigned char c : text) {
		output += "0123456789abcdef"[c >> 4];
		output += "0123456789abcdef"[c & 15];
	}
	return output;
}

inline bool Unhex(std::string_view text, std::string &output, std::size_t limit = 63)
{
	if (text.empty() || text.size() % 2 || text.size() / 2 > limit) { return false; }
	std::string decoded;
	auto nibble = [](char c) { return c >= '0' && c <= '9' ? c - '0' : c >= 'a' && c <= 'f' ? c - 'a' + 10 : -1; };
	for (std::size_t i = 0; i < text.size(); i += 2) {
		const int high = nibble(text[i]), low = nibble(text[i + 1]);
		if (high < 0 || low < 0) { return false; }
		const int c = high * 16 + low;
		if (c < 32 || c > 126) { return false; }
		decoded += static_cast<char>(c);
	}
	output = std::move(decoded);
	return true;
}

inline bool Fields(std::string_view text, std::vector<std::string_view> &fields)
{
	if (text.size() > MaxMessage) { return false; }
	fields.clear();
	std::size_t start = 0;
	while (start <= text.size()) {
		if (fields.size() == 16) { return false; }
		const auto end = text.find('|', start);
		fields.push_back(text.substr(start, end == std::string_view::npos ? text.size() - start : end - start));
		if (end == std::string_view::npos) { break; }
		start = end + 1;
	}
	return true;
}

struct Identity {
	uint32_t character = 0, zone = 0, instance = 0, spawn = 0;
	std::string name;
	bool operator==(const Identity &other) const {
		return character == other.character && zone == other.zone && instance == other.instance && spawn == other.spawn && name == other.name;
	}
};

struct Row {
	uint32_t token = 0, corpse = 0, item = 0, quantity = 0, icon = 0, capabilities = 0;
	Phase phase = Phase::Personal;
	Filter filter = Filter::Ask;
	std::string name, source;
};

struct Snapshot {
	uint32_t session = 0, revision = 0, settings = 0, page = 0, total = 0;
	View view = View::Drops;
	Identity identity;
	std::vector<Row> rows;
};

inline std::string Begin(const Snapshot &s)
{
	return "[NCAL1]B|" + std::to_string(s.session) + "|" + std::to_string(s.revision) + "|" +
		std::to_string(s.identity.character) + "|" + std::to_string(s.identity.zone) + "|" +
		std::to_string(s.identity.instance) + "|" + std::to_string(s.identity.spawn) + "|" +
		std::to_string(s.settings) + "|" + std::to_string(static_cast<uint32_t>(s.view)) + "|" +
		std::to_string(s.page) + "|" + std::to_string(s.total) + "|" + Hex(s.identity.name);
}

inline std::string Item(const Snapshot &s, const Row &r)
{
	return "[NCAL1]I|" + std::to_string(s.session) + "|" + std::to_string(s.revision) + "|" +
		std::to_string(r.token) + "|" + std::to_string(r.corpse) + "|" + std::to_string(r.item) + "|" +
		std::to_string(r.quantity) + "|" + std::to_string(r.icon) + "|" + std::to_string(r.capabilities) + "|" +
		std::to_string(static_cast<uint32_t>(r.phase)) + "|" + std::to_string(static_cast<uint32_t>(r.filter)) + "|" +
		Hex(r.name) + "|" + Hex(r.source);
}

inline std::string End(const Snapshot &s)
{
	return "[NCAL1]E|" + std::to_string(s.session) + "|" + std::to_string(s.revision) + "|" + std::to_string(s.rows.size());
}
}
