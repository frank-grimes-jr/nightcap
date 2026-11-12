#pragma once
#include "common/raid_augment.h"
#include <algorithm>
#include <cstdint>

class Client;
class Mob;
class NPC;
namespace NightcapRaidAug {
struct State {
	uint32_t item = 0;
	int socket = -1;
	int64_t mana_spent = 0, endurance_spent = 0;
	int ward = 0;
	uint32_t ward_started = 0;
	void ClearSpend() { mana_spent = endurance_spent = 0; }
	void Equip(uint32_t next, int index) {
		if (item != next || socket != index) { *this = {}; item = next; socket = index; }
	}
};
// Nested procs and reflected spells must not inherit a gem cast's provenance.
struct CastOrigin {
	const Mob *caster;
	uint32_t spell;
	bool gem;
	bool triggered;
	bool discipline;
	const CastOrigin *previous;
	static thread_local const CastOrigin *current;
	CastOrigin(const Mob *who, uint32_t id, bool direct, bool indirect = false, bool disc = false) :
		caster(who), spell(id), gem(direct), triggered(indirect), discipline(disc), previous(current) { current = this; }
	~CastOrigin() { current = previous; }
};
inline int64_t Refund(int64_t &spent, int64_t paid, int64_t maximum)
{
	if (paid <= 0 || maximum < 100) { return 0; }
	const auto threshold = maximum / 10 + (maximum % 10 != 0);
	spent = std::min(spent, threshold) + std::min(paid, threshold);
	return spent >= threshold ? std::min<int64_t>(50, maximum / 100) : 0;
}

void Refresh(Client &c);
void Incoming(Client &c, Mob *attacker, int64_t &damage);
void AfterHit(Mob &target, Mob *attacker, int64_t damage, uint16_t spell, bool direct_weapon);
bool IsExchangeSpell(uint16_t spell);
void Spend(Client &c, int64_t paid, bool mana);
}
