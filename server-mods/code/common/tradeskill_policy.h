#pragma once

#include <algorithm>
#include <cstdint>
#include <map>
#include <set>
#include <vector>

namespace NightcapTradeskill {
struct Ingredient { uint32_t item_id, quantity; };
struct Stack { uint16_t slot; uint32_t item_id, quantity; };
struct Use { uint16_t slot; uint32_t quantity; };

// Physical units, never charges of a nonstackable item. Build the entire plan
// before changing inventory; duplicate ingredient rows share one requirement.
inline bool Plan(const std::vector<Stack>& stacks, const std::vector<Ingredient>& ingredients,
	std::vector<Use>& uses, bool exact_types = true)
{
	uses.clear();
	if (ingredients.empty() || ingredients.size() > 10) { return false; }
	std::map<uint32_t, uint32_t> remaining;
	for (const auto& item : ingredients) {
		if (!item.item_id || !item.quantity || item.quantity > 10000 ||
			remaining[item.item_id] > 10000 - item.quantity) { return false; }
		remaining[item.item_id] += item.quantity;
	}
	std::set<uint16_t> slots;
	for (const auto& stack : stacks) {
		if (!stack.item_id || !stack.quantity || !slots.insert(stack.slot).second) { return false; }
		if (exact_types && !remaining.count(stack.item_id)) { return false; }
	}
	std::vector<Use> result;
	for (const auto& stack : stacks) {
		auto found = remaining.find(stack.item_id);
		if (found == remaining.end() || !found->second) { continue; }
		const auto amount = std::min(found->second, stack.quantity);
		result.push_back({stack.slot, amount});
		found->second -= amount;
	}
	for (const auto& item : remaining) { if (item.second) { return false; } }
	uses = std::move(result);
	return true;
}

inline bool Exact(const std::vector<Stack>& stacks, const std::vector<Use>& uses)
{
	if (stacks.size() != uses.size()) { return false; }
	for (size_t i = 0; i < stacks.size(); ++i) {
		if (stacks[i].slot != uses[i].slot || stacks[i].quantity != uses[i].quantity) { return false; }
	}
	return true;
}
}
