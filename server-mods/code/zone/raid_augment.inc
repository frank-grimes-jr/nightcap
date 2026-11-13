// Included by zone_hunt.cpp so source-overlay builds pick up the implementation.
namespace NightcapRaidAug {
thread_local const CastOrigin *CastOrigin::current = nullptr;

void Refresh(Client &c)
{
	const auto *host = c.GetInv().GetItem(EQ::invslot::slotChest);
	uint32_t found = 0;
	int selected = -1;
	if (c.GetLevel() >= Level && host && host->IsClassCommon() && IsHost(host->GetItem()->Slots) &&
		c.CanEquipItem(host->GetItem()) && c.GetLevel() >= host->GetItemRequiredLevel(true)) {
		for (int i = 0; i < EQ::invaug::SOCKET_COUNT; ++i) {
			if (host->GetItem()->AugSlotType[i] != SocketType) { continue; }
			const auto id = host->GetAugmentItemID(i);
			if (IsReward(id)) { found = id; selected = i; break; }
		}
	}
	c.raid_augment.Equip(found, selected);
}

static bool Ready(Client &c)
{
	return c.GetPTimers().GetRemainingTime(pTimerRaidAugment) == 0;
}

static bool Activate(Client &c)
{
	if (!Ready(c)) { return false; }
	auto &timers = c.GetPTimers();
	// Persistent timers truncate the start to whole seconds. Round the expiry up
	// so swaps and reconnects cannot shorten the 90-second minimum.
	timers.Start(pTimerRaidAugment, 91);
	// Persist before granting any benefit, including across disconnect/crash.
	return timers.Get(pTimerRaidAugment)->Store(&database);
}

void Incoming(Client &c, Mob *attacker, int64_t &damage)
{
	auto &state = c.raid_augment;
	if (state.item != Aegis || damage <= 0 || !attacker || !attacker->IsNPC() || attacker == &c) { return; }
	if (state.ward && static_cast<uint32_t>(Timer::GetCurrentTime() - state.ward_started) < 12000) {
		const int absorbed = static_cast<int>(std::min<int64_t>(damage, state.ward));
		damage -= absorbed;
		state.ward -= absorbed;
	}
}

void AfterHit(Mob &target, Mob *attacker, int64_t damage, uint16_t spell, bool direct_weapon)
{
	if (damage <= 0 || !attacker || &target == attacker) { return; }
	const auto *cast = CastOrigin::current;
	if (target.IsClient() && attacker->IsNPC() && !attacker->HasOwner() &&
		!attacker->CastToNPC()->GetSwarmOwner() && !(cast && cast->triggered) &&
		(direct_weapon || (cast && cast->caster == attacker && cast->spell == spell))) {
		auto &c = *target.CastToClient();
		if (c.raid_augment.item == Aegis && c.GetHP() > 0 && c.GetHP() * 100 < c.GetMaxHP() * 35) {
			// Existing ordinary runes absorb first. Never replace or compound a stronger ward.
			for (int i = 0; i < c.GetMaxTotalSlots(); ++i) {
				const auto &buff = c.GetBuffs()[i];
				if (IsValidSpell(buff.spellid) && (buff.melee_rune >= 120 || buff.magic_rune >= 120)) { return; }
			}
			if (Activate(c)) {
				c.raid_augment.ward = 120;
				c.raid_augment.ward_started = Timer::GetCurrentTime();
				c.Message(Chat::Spells, "Faceless Aegis wards you against 120 damage.");
			}
		}
	}
	if (!attacker->IsClient() || !target.IsNPC() || target.GetUltimateOwner()->IsClient()) { return; }
	auto &c = *attacker->CastToClient();
	if (c.raid_augment.item != Heart || c.GetHP() <= 0 || c.GetHP() >= c.GetMaxHP()) { return; }
	const bool gem = cast && cast->gem && cast->caster == &c && cast->spell == spell;
	if (((direct_weapon && !cast) || gem) && Activate(c)) {
		const auto healed = std::min<int64>(90, c.GetMaxHP() - c.GetHP());
		c.SetHP(c.GetHP() + healed);
		c.SendHPUpdate();
		c.Message(Chat::Spells, "Heart of Spite restores %d HP.", static_cast<int>(healed));
	}
}

void Spend(Client &c, int64_t paid, bool mana)
{
	auto &state = c.raid_augment;
	if (state.item != Prism || !c.GetAggroCount() || paid <= 0 || !Ready(c)) { return; }
	auto &spent = mana ? state.mana_spent : state.endurance_spent;
	const auto restore = Refund(spent, paid, mana ? c.GetMaxMana() : c.GetMaxEndurance());
	if (restore && Activate(c)) {
		state.ClearSpend();
		if (mana) { c.SetMana(c.GetMana() + restore); }
		else { c.SetEndurance(c.GetEndurance() + restore); }
		c.Message(Chat::Spells, "Prism of the Eighth Isle restores %d %s.", static_cast<int>(restore), mana ? "mana" : "endurance");
	}
}
}
