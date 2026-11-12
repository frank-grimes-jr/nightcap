// Included by aa.cpp. Keep native cast completion: reagents, stacking, range,
// group/pet delivery and spell events still run for every memorized buff.
void Client::CastQuickBuff(int rank_id)
{
	if (m_quick_buff_active || IsDead() || IsUnconscious() || IsCasting() || delaytimer || spellend_timer.Enabled()) {
		Message(Chat::Red, "You cannot use Quick Buff right now.");
		return;
	}
	const int32 cost = NightcapQuickBuff::ManaCost(GetMaxMana());
	if (cost <= 0 || GetMana() < cost) {
		Message(Chat::Red, "Quick Buff requires 50 percent of your maximum mana.");
		return;
	}
	if (GetAppearance() == eaSitting) { SetAppearance(eaStanding, false); }
	if (GetAppearance() != eaStanding) { return; }

	std::vector<uint16> buffs;
	std::set<int> seen;
	for (const int id : GetMemmedSpells()) {
		if (!IsValidSpell(id) || !seen.insert(id).second || !IsBeneficialSpell(id) ||
			!IsBuffSpell(id) || IsDiscipline(id) || !HasSpellScribed(id) ||
			GetSpellMinLevel(id) == 255 || GetLevel() < GetSpellMinLevel(id)) {
			continue;
		}
		const bool pet_spell = spells[id].target_type == ST_Pet || spells[id].target_type == ST_SummonedPet;
		Mob *recipient = pet_spell ? GetPet() : this;
		if (!recipient) { continue; }
		if (!DoCastingChecksOnCaster(id, EQ::spells::CastingSlot::AltAbility) ||
			!DoCastingChecksZoneRestrictions(true, id) ||
			!DoCastingChecksOnTarget(true, id, recipient)) {
			continue;
		}
		buffs.push_back(static_cast<uint16>(id));
	}
	if (buffs.empty()) {
		Message(Chat::Red, "You have no eligible buffs memorized for Quick Buff.");
		return;
	}

	// Debit before spell/quest callbacks; recursive activation cannot obtain a
	// second batch or avoid the flat cost. Individual spell mana costs are zero.
	m_quick_buff_active = true;
	struct Guard { bool &active; ~Guard() { active = false; } } guard{m_quick_buff_active};
	SetMana(GetMana() - cost);
	CommonBreakInvisible();
	for (const uint16 id : buffs) {
		const bool pet_spell = spells[id].target_type == ST_Pet || spells[id].target_type == ST_SummonedPet;
		if (pet_spell && !GetPet()) { continue; }
		CastSpell(id, pet_spell ? GetPetID() : GetID(), EQ::spells::CastingSlot::AltAbility,
			0, 0, nullptr, -1, pTimerAAStart + NightcapQuickBuff::Family, 0, nullptr, rank_id);
	}
	p_timers.Clear(&database, pTimerAAStart + NightcapQuickBuff::Family);
	SendAlternateAdvancementTimer(NightcapQuickBuff::Family, 0, 0);
}
