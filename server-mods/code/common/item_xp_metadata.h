#pragma once
#include "item_xp_policy.h"
#include <map>
#include <string>

namespace NightcapItemXP {
struct Metadata {
	bool valid = false;
	bool present = false;
	uint64_t progress = 0;
	std::map<std::string, std::string> fields;
};

inline bool Decimal(const std::string &text, uint64_t maximum, uint64_t &value)
{
	if (text.empty() || (text.size() > 1 && text[0] == '0')) { return false; }
	value = 0;
	for (const char ch : text) {
		if (ch < '0' || ch > '9' || value > maximum / 10 ||
			(value == maximum / 10 && uint64_t(ch - '0') > maximum % 10)) { return false; }
		value = value * 10 + uint64_t(ch - '0');
	}
	return true;
}

inline std::string Encode(const std::map<std::string, std::string> &fields)
{
	std::string result;
	for (const auto &field : fields) {
		if (!result.empty()) { result += '^'; }
		result += field.first + '^' + field.second + '^';
	}
	return result;
}

// Accept exactly the native saved representation. This avoids silently
// normalizing another system's metadata during an inventory compare-and-swap.
inline Metadata ReadMetadata(const std::string &data, uint32_t item_id, uint8_t tier)
{
	Metadata result;
	size_t position = 0;
	while (position < data.size()) {
		const auto key_end = data.find('^', position);
		if (key_end == std::string::npos || key_end == position) { return {}; }
		const auto value_end = data.find('^', key_end + 1);
		if (value_end == std::string::npos) { return {}; }
		const auto key = data.substr(position, key_end - position);
		if (!result.fields.emplace(key, data.substr(key_end + 1, value_end - key_end - 1)).second) { return {}; }
		position = value_end + 1;
		if (position < data.size()) {
			if (data[position] != '^' || ++position == data.size()) { return {}; }
		}
	}
	if (Encode(result.fields) != data || tier > 3) { return {}; }
	const auto field = result.fields.find(Key);
	if (field != result.fields.end()) {
		result.present = true;
		const auto prefix = "1:" + std::to_string(item_id) + ':';
		if (field->second.compare(0, prefix.size(), prefix) ||
			!Decimal(field->second.substr(prefix.size()), MaxProgress, result.progress)) { return {}; }
	}
	if (!Advance(tier, result.progress, 0).valid) { return {}; }
	result.valid = true;
	return result;
}

inline std::string WriteMetadata(Metadata metadata, uint32_t item_id, uint64_t progress)
{
	if (progress) { metadata.fields[Key] = "1:" + std::to_string(item_id) + ':' + std::to_string(progress); }
	else { metadata.fields.erase(Key); }
	return Encode(metadata.fields);
}
}
