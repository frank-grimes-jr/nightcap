// Included by command.cpp; uses the zone's loaded faction cache and caller only.
void command_factions(Client *c, const Seperator *sep)
{
	const auto request = NightcapFaction::Parse(sep->argplus[1]);
	if (!request.valid) {
		c->Message(Chat::White, "Usage: #factions [page] [name] or #factions target. Use a positive page and at most 80 characters.");
		return;
	}
	int32 target_faction = 0;
	if (request.target) {
		auto *target = c->GetTarget();
		if (!target || !target->IsNPC() || target->GetPrimaryFaction() <= 0) {
			c->Message(Chat::White, "Target an NPC with a normal faction, then use #factions target. Special reactions have no numerical faction standing.");
			return;
		}
		target_faction = target->GetPrimaryFaction();
	}
	std::vector<NightcapFaction::Entry> entries;
	const auto last = request.target ? static_cast<uint32>(target_faction) : content_db.GetMaxFaction();
	for (uint32 id = request.target ? static_cast<uint32>(target_faction) : 1; id <= last; ++id) {
		const auto name = content_db.GetFactionName(id);
		if (name.empty() || !NightcapFaction::Matches(name, request.filter)) { continue; }
		FactionMods mods{};
		if (!content_db.GetFactionData(&mods, c->GetClass(), c->GetFactionRace(), c->GetDeity(), id)) { continue; }
		const auto earned = c->GetCharacterFactionLevel(id);
		const auto total = c->GetModCharacterFactionLevel(id);
		const auto adjustment = total - earned;
		// Match SetFactionLevel/SetFactionLevel2's actual personal bounds.
		const auto minimum = std::min(0, mods.min - mods.base) + adjustment;
		const auto maximum = std::max(0, mods.max - mods.base) + adjustment;
		entries.push_back({static_cast<int32>(id), name, FactionValueToString(CalculateFaction(nullptr, total)), earned, total, minimum, maximum});
	}
	std::sort(entries.begin(), entries.end(), [](const auto &a, const auto &b) {
		const auto left = NightcapFaction::Lower(a.name);
		const auto right = NightcapFaction::Lower(b.name);
		return left == right ? a.id < b.id : left < right;
	});
	const auto text = NightcapFaction::Render(entries, request);
	// The native OnLevelMessage text field is 4096 bytes, including NUL.
	if (text.size() >= 4096) {
		c->Message(Chat::White, "Faction display is too large. Please narrow your name search.");
		return;
	}
	c->SendPopupToClient("Faction Standings", text.c_str());
}
