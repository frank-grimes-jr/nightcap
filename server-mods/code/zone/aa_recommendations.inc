// Included in aa.cpp so the tracked overlay remains self-contained.
void Client::SendAARecommendations()
{
	using namespace nightcap::recommended_aa;
	if (!zone || !m_nightcap_ui_enabled || !m_nightcap_aa_recommendations_enabled ||
		!m_nightcap_ui_generation || !HasValidEarnedAAState()) { return; }
	std::vector<Choice> choices;
	for (const auto &entry : kEntries) {
		auto ability = zone->GetAlternateAdvancementAbility(entry.ability);
		if (!ability || ability->charges || ability->grant_only) { continue; }
		uint32 charges = 0;
		const auto owned = GetAA(ability->first_rank_id, &charges);
		const auto maximum = ability->GetMaxLevel(this);
		if (owned >= maximum) { continue; }
		auto rank = ability->GetRankByPointsSpent(owned + 1);
		if (!rank || !CanUseAlternateAdvancementRank(rank) || HasAlreadyPurchasedRank(rank)) { continue; }
		bool useful = true;
		switch (entry.gate) {
		case MonkSpecial: useful = GetSkill(EQ::skills::SkillRoundKick) || GetSkill(EQ::skills::SkillTigerClaw) ||
			GetSkill(EQ::skills::SkillEagleStrike) || GetSkill(EQ::skills::SkillDragonPunch) || GetSkill(EQ::skills::SkillFlyingKick); break;
		case Mend: useful = GetSkill(EQ::skills::SkillMend) > 0; break;
		case Backstab: useful = GetSkill(EQ::skills::SkillBackstab) > 0; break;
		case Archery: useful = GetSkill(EQ::skills::SkillArchery) > 0; break;
		case Throwing: useful = GetSkill(EQ::skills::SkillThrowing) > 0; break;
		case nightcap::recommended_aa::Pet:
			useful = GetPet() != nullptr;
			for (const auto class_id : GetMulticlassList()) { useful = useful || GetClassPet(class_id) != 0; }
			break;
		default: break;
		}
		const auto target = std::min<int>(maximum, entry.target);
		const auto priority = entry.priority + (owned >= static_cast<uint32>(target) ? 100 : 0);
		const bool ready = CanPurchaseAlternateAdvancementRank(rank, false, true);
		choices.push_back({static_cast<uint32>(rank->id),static_cast<uint32>(ability->id),
			static_cast<uint32>(owned >= static_cast<uint32>(target) ? maximum : target),
			static_cast<uint32>(entry.reason),useful ? (ready ? 0u : 1u) : 2u,priority});
		// Add the next legal step of each unmet prerequisite. Never pretend that
		// a blocked desired rank is currently trainable or unlock it for the UI.
		for (const auto &prereq : rank->prereqs) {
			auto required = zone->GetAlternateAdvancementAbility(prereq.first);
			if (!required) { continue; }
			const auto have = GetAA(required->first_rank_id, &charges);
			if (have >= static_cast<uint32>(prereq.second)) { continue; }
			auto next = required->GetRankByPointsSpent(have + 1);
			if (!next || !CanUseAlternateAdvancementRank(next) || !CanPurchaseAlternateAdvancementRank(next, false, true)) { continue; }
			choices.push_back({static_cast<uint32>(next->id),static_cast<uint32>(required->id),
				static_cast<uint32>(prereq.second),25,useful ? 0u : 2u,priority});
		}
	}
	const auto rows = Select(std::move(choices));
	const auto identity = fmt::format("{}|{}|{}|{}|{}",m_nightcap_ui_generation,CharacterID(),
		zone->GetZoneID(),zone->GetInstanceID(),GetID());
	std::string content;
	for (const auto &row : rows) {
		content += fmt::format("[NCUI1]R|{}|{}|{}|{}|{}\n",identity,row.rank,row.reason,row.status,row.target);
	}
	const auto cache = identity + "\n" + content;
	if (cache == m_nightcap_aa_recommendations_cache) { return; }
	m_nightcap_aa_recommendations_cache = cache;
	Message(Chat::White,"[NCUI1]B|%s|%u",identity.c_str(),static_cast<uint32>(rows.size()));
	for (const auto &row : rows) {
		Message(Chat::White,"[NCUI1]R|%s|%u|%u|%u|%u",identity.c_str(),row.rank,row.reason,row.status,row.target);
	}
	Message(Chat::White,"[NCUI1]E|%s",identity.c_str());
}
