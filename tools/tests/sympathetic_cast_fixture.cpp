// test_sympathetic_cast.py inserts the actual native methods and dispatch blocks.
#include "nightcap_sympathetic.h"
#include "nightcap_heroic_cast.h"
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <map>

using namespace NightcapSympathetic;
using uint16 = uint16_t;
using uint32 = uint32_t;
using int64 = int64_t;
namespace EQ::spells { enum class CastingSlot { Gem, MaxGems = 12, Item = 22, AltAbility = 255 }; }
using EQ::spells::CastingSlot;
namespace SpellEffect { enum { CurrentHP, PercentalHeal, CompleteHeal }; }
namespace NumHit { constexpr int MatchingSpells = 1; }
constexpr int focusSympatheticProc = 1;
int era = 0;
#define RuleI(category, rule) era

struct Spell {
	int mana = 10, skill = 0, resist_difficulty = 0, limit_value[1]{}, base_value[1]{}, max_value[1]{};
	bool good = false, duration = false, song = false, dot = false, group = false, is_discipline = false;
};
Spell spells[65536];
bool IsValidSpell(int id) { return id > 0 && id < 65535; }
bool IsBeneficialSpell(int id) { return spells[id].good; }
bool IsDetrimentalSpell(int id) { return !spells[id].good; }
bool IsBuffSpell(int id) { return spells[id].duration; }
bool IsBardSong(int id) { return spells[id].song; }
bool IsInstantCastDot(int id) { return spells[id].dot; }
bool IsGroupSpell(int id) { return spells[id].group; }

struct EntityList {
	std::map<uint16, Mob *> mobs;
	Mob *GetMob(uint16 id) { return mobs[id]; }
} entity_list;

class Mob {
public:
	explicit Mob(int id) : id(id) { entity_list.mobs[id] = this; }
	uint16 id, source_spell = 0;
	int hp = 500, maxhp = 2000, outgoing_factor = 1, casting_spell_aa_id = 0;
	int hit_count = 0, heal_count = 0, focus_hits = 0, focus_rolls = 0, resource = 0;
	int focus = 0, child = 50;
	bool client = true, dead = false, depop = false, corpse = false, restricted = false;
	bool strike = true, healing = true, worn = true, block_focus = false, block_target = false;
	bool group_focus = false, nested_heal = false;
	Mob *second_recipient = nullptr, *selected_target = nullptr;
	struct Profile { int mem_spells[12]{}; } pp;
	Profile &GetPP() { return pp; }
	Mob *CastToClient() { return this; }
	Mob *CastToNPC() { return this; }
	bool IsClient() { return client; }
	bool IsOfClientBotMerc() { return client; }
	bool IsNPC() { return !client; }
	bool IsCorpse() { return corpse; }
	bool IsDead() { return dead; }
	bool GetDepop() { return depop; }
	int GetHP() { return hp; }
	int GetMaxHP() { return maxhp; }
	uint16 GetID() { return id; }
	bool FindBuff(int id) { return id == StrikeBuff ? strike : id == HealingBuff && healing; }
	bool PassCastRestriction(int) { return !restricted; }
	int GetActSpellDamage(int, int damage, Mob *) { return damage * outgoing_factor; }
	int GetActSpellHealing(int, int heal, Mob *) { return heal * outgoing_factor; }
	int GetActReflectedSpellDamage(int, int damage, int) { return damage; }
	void GetActDoTDamage(int, int, Mob *, bool) {}
	void ResourceTap(int damage, int) { resource += damage; }
	void Damage(Mob *caster, int64 damage, uint16 spell, int, bool, int = -1, bool = false) {
		++hit_count;
		hp -= static_cast<int>(damage);
		source_spell = spell;
		if (spell == 9) { caster->HealDamage(damage, caster, spell); }
	}
	void HealDamage(int64 heal, Mob *, uint16 spell = 0) {
		++heal_count;
		hp = std::min<int>(maxhp, hp + static_cast<int>(heal));
		source_spell = spell;
	}
	int GetSympatheticFocusEffect(int, int, bool &source) { ++focus_rolls; source = worn; return focus; }
	int GetSympatheticSpellProcID(int) { return child; }
	void CheckNumHitsRemaining(int, int, int) { ++focus_hits; }

	Effect Gem(int spell_id, CastingSlot slot = CastingSlot::Gem) {
		/* ORIGINAL GEM CHECK */
		return sympathetic.effect;
	}
	void SpellEffect(Mob *caster, uint16 spell_id, int effect_value, int effect, int buffslot = -2, int reflect_effectiveness = 0) {
		/* RECORD HP */
		auto &spell = spells[spell_id];
		int partial = 100, i = 0;
		switch (effect) {
			/* CURRENT HP */
			/* HEAL EFFECTS */
		}
	}
	void OnTarget(Mob *spelltar, int spell_id, int value, int spell_effectiveness = 100, int reflect_effectiveness = 0,
		int effect = SpellEffect::CurrentHP, bool isproc = false) {
		/* TARGET RECEIPT */
		if (nested_heal) { nested_heal = false; OnTarget(this, spell_id, 10); }
		if (spelltar->block_target) { return; }
		/* LANDING */
		Cast::Deliver(receipt, [&] { spelltar->SpellEffect(this, spell_id, value, effect, -2, reflect_effectiveness); return true; });
	}
	bool SpellFinished(int spell_id, Mob *to, CastingSlot = CastingSlot::Item, int = 0, int = -1, int = 0) {
		auto *sympathetic = Cast::Take();
		const WornGroup nested_group;
		// Blocked buffs return success to the casting client without applying effects.
		if (block_focus) { return true; }
		if (group_focus) {
			/* GROUP WORN RECEIPT */
			OnTarget(to, spell_id, 80); OnTarget(second_recipient, spell_id, 80);
		} else {
			Cast::Deliver(sympathetic, [&] { OnTarget(selected_target ? selected_target : to, spell_id, 80); return true; });
		}
		return true;
	}
	void TrySympatheticProc(Mob *, uint32);
	void ApplySympatheticClick(const Cast &);
};

/* PROC AND APPLICATION */

int main()
{
	for (auto line : {Line::Strike, Line::Healing}) {
		for (const auto &[hp, expected] : std::map<int64, int>{{0,0},{19,0},{20,1},{39,1},{40,2},
			{959,47},{960,48},{961,48},{INT64_MAX,48}}) {
			Cast rank;
			rank.effect = line == Line::Strike ? Effect::Strike : Effect::Healing;
			rank.Record(line, hp);
			assert(rank.Bonus() == expected && rank.landed == (hp > 0));
			rank.Record(line, 0);
			assert(rank.Bonus() == expected);
		}
	}
	Cast tiny_worn; tiny_worn.effect = Effect::WornHeal;
	tiny_worn.Record(Line::Healing, 1);
	assert(tiny_worn.landed && tiny_worn.Bonus() == 0);
	Mob caster(1), pet(2), selected(3);
	pet.client = false;
	constexpr int tap = 9, heal = 20;
	spells[heal].good = spells[50].good = true;
	caster.pp.mem_spells[0] = tap;
	assert(caster.Gem(tap) == Effect::Strike && caster.Gem(heal) == Effect::None);
	assert(caster.Gem(tap, CastingSlot::AltAbility) == Effect::None && caster.Gem(tap, CastingSlot::Item) == Effect::None);
	spells[tap].mana = 9;
	assert(caster.Gem(tap) == Effect::None);
	spells[tap].mana = 10;
	// An instant DD plus a timed debuff is still a duration-bearing hybrid.
	spells[tap].duration = true;
	assert(caster.Gem(tap) == Effect::None);
	spells[tap].duration = false;
	for (auto field : {&Spell::duration, &Spell::song, &Spell::dot, &Spell::group, &Spell::is_discipline}) {
		spells[tap].*field = true;
		assert(caster.Gem(tap) == Effect::None);
		spells[tap].*field = false;
	}
	caster.casting_spell_aa_id = 1; assert(caster.Gem(tap) == Effect::None); caster.casting_spell_aa_id = 0;
	caster.client = false; assert(caster.Gem(tap) == Effect::None); caster.client = true;
	caster.strike = false; assert(caster.Gem(tap) == Effect::None); caster.strike = true;
	caster.pp.mem_spells[0] = heal; spells[heal].mana = 0; assert(caster.Gem(heal) == Effect::None);
	spells[heal].mana = 1; assert(caster.Gem(heal) == Effect::Healing);

	auto deliver = [&](Cast &cast, Mob &recipient, int spell, int value, int percent = 100, int reflection = 0) {
		Cast::Deliver(&cast, [&] { caster.OnTarget(&recipient, spell, value, percent, reflection); return true; });
	};
	auto worn = [&](Cast &cast) {
		Cast::Deliver(&cast, [&] { caster.TrySympatheticProc(&selected, heal); return true; });
	};
	Cast original; original.effect = Effect::Strike;
	caster.outgoing_factor = 3;
	deliver(original, pet, tap, -20, 75); assert(!original.landed);
	deliver(original, pet, tap, -20, 100, 30); assert(!original.landed);
	spells[tap].limit_value[0] = 1; pet.restricted = true;
	deliver(original, pet, tap, -20); assert(!original.landed);
	pet.restricted = false; int before = pet.hp;
	deliver(original, pet, tap, -20); deliver(original, pet, tap, -10);
	int self_hp = caster.hp, resource = caster.resource;
	caster.ApplySympatheticClick(original);
	assert(pet.hp == before - 90 - 3 && pet.source_spell == StrikeBuff);
	assert(caster.hp == self_hp && caster.resource == resource);
	for (bool *flag : {&pet.depop, &pet.corpse}) {
		*flag = true; before = pet.hp; caster.ApplySympatheticClick(original); assert(before == pet.hp); *flag = false;
	}
	era = -2; before = pet.hp; caster.ApplySympatheticClick(original); assert(pet.hp == before); era = 0;
	entity_list.mobs[pet.id] = &selected; caster.ApplySympatheticClick(original);
	assert(pet.hp == before); entity_list.mobs[pet.id] = &pet;

	Cast restoration; restoration.effect = Effect::Healing; caster.focus = 51;
	deliver(restoration, pet, heal, 25); before = pet.hp;
	selected.hp = selected.maxhp;
	worn(restoration);
	assert(restoration.worn_heal && caster.focus_hits == 1 && caster.focus_rolls == 1);
	caster.ApplySympatheticClick(restoration);
	assert(pet.hp == before && selected.hp == selected.maxhp);
	caster.block_focus = true; restoration.worn_heal = false; worn(restoration);
	assert(!restoration.worn_heal && caster.focus_hits == 2 && caster.focus_rolls == 2);
	caster.ApplySympatheticClick(restoration);
	assert(pet.hp == before + 3 && pet.source_spell == HealingBuff);
	caster.block_focus = false; caster.worn = false; caster.focus = 51; restoration.worn_heal = false;
	worn(restoration); assert(!restoration.worn_heal && caster.focus_hits == 3);
	caster.focus = 0; worn(restoration); assert(!restoration.worn_heal && caster.focus_hits == 3);
	Cast self; self.effect = Effect::Healing; deliver(self, caster, heal, 2);
	before = caster.hp; caster.ApplySympatheticClick(self); assert(caster.hp == before);
	for (int direct_effect : {SpellEffect::CompleteHeal, SpellEffect::PercentalHeal}) {
		Cast positive; positive.effect = Effect::Healing;
		spells[heal].base_value[0] = 5;
		Cast::Deliver(&positive, [&] { caster.OnTarget(&pet, heal, 1, 100, 0, direct_effect); return true; });
		assert(positive.landed && positive.recipient == &pet);
	}
	Cast tick; tick.effect = Effect::Strike;
	Cast::Deliver(&tick, [&] { pet.SpellEffect(&caster, tap, -25, SpellEffect::CurrentHP, 2); return true; });
	assert(!tick.landed);
	Mob group_member(4);
	caster.worn = true; caster.focus = 51; caster.group_focus = true; caster.second_recipient = &group_member;
	selected.block_target = true;
	group_member.hp = group_member.maxhp;
	Cast group_case; group_case.effect = Effect::Healing; deliver(group_case, pet, heal, 40);
	worn(group_case); assert(group_case.worn_heal);  // Second member accepted, including full HP.
	before = pet.hp; caster.ApplySympatheticClick(group_case); assert(pet.hp == before);
	group_member.block_target = true; caster.nested_heal = true;
	group_case.worn_heal = false; worn(group_case); assert(!group_case.worn_heal);
	caster.ApplySympatheticClick(group_case); assert(pet.hp == std::min(pet.maxhp, before + 6));
	caster.group_focus = false; caster.selected_target = &group_member;
	group_member.block_target = false; group_case.worn_heal = false;
	worn(group_case); assert(group_case.worn_heal);

	Cast::Deliver(&original, [&] {
		assert(Cast::Take() == &original && Cast::Take() == nullptr);
		Cast::Deliver(&restoration, [&] { assert(Cast::Take() == &restoration); return true; });
		assert(Cast::Take() == nullptr); return true;
	});
	assert(Cast::Take() == nullptr);
	struct Projectile { int ammo_slot; uint32 ranged_id; bool disable_procs; } bolt{99, 92, true};
	StoreBolt(bolt, Effect::Strike, 12);
	assert(BoltEffect(bolt, 12) == Effect::Strike && BoltEffect(bolt, 13) == Effect::None);
	StoreBolt(bolt, Effect::Healing, 13); bolt.disable_procs = true;
	assert(BoltEffect(bolt, 13) == Effect::None);
	StoreBolt(bolt, Effect::None, 12); assert(BoltEffect(bolt, 12) == Effect::None && !bolt.disable_procs);
}
