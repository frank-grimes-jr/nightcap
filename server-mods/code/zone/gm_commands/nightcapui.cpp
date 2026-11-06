#include "zone/client.h"
#include "zone/command.h"
#include "common/seperator.h"
#include "common/rulesys.h"
#include "zone/zone_hunt.h"

// Self-only, read-only view of calculated server bonuses. Never reconstruct
// active bonuses by summing bagged items or the client's stock stat-cap display.
void command_augstats(Client *c, const Seperator *)
{
	const auto item = c->GetItemBonuses();
	const auto spell = c->GetSpellBonuses();
	const auto aa = c->GetAABonuses();
	const int block = c->HasShieldEquipped() ? item.ShieldBlock + spell.ShieldBlock + aa.ShieldBlock : 0;
	const auto text = fmt::format(
		"<c \"#FFFFFF\">Equipped combat bonuses</c><br>"
		"Shield Block: {}% (nominal frontal block check)<br>"
		"Hunt augments: +{}%; strongest only.<br>"
		"Block components: Items {}%, Spells {}%, AAs {}%.<br>"
		"A shield is required; attack counters and facing can alter the check.<br><br>"
		"Shielding: {} / {}% (melee damage reduction; separate from block)<br>"
		"Spell Shielding: {} / {}%<br>"
		"Avoidance: {} / {}<br>Accuracy: {} / {}<br>"
		"Spell Damage: {} / {}<br>Heal Amount: {} / {}<br>"
		"Dodge modifier: +{}% (relative skill modifier, not flat avoidance)<br><br>"
		"These are current server totals/caps, including equipment beyond augments. "
		"Bagged and Power Source training items contribute nothing.<br>"
		"HP, mana, attributes and numeric item bonuses add up within caps. "
		"Repeated Hunt shield block, spell focuses, Improved Dodge I and Faerune "
		"do not multiply their same effect. Focus strength also depends on the spell's limits.",
		block, NightcapHunt::OutputShieldBlock(*c), item.ShieldBlock, spell.ShieldBlock, aa.ShieldBlock,
		c->GetShielding(), RuleI(Character, ItemShieldingCap), c->GetSpellShield(), RuleI(Character, ItemSpellShieldingCap),
		c->GetAvoidance(), RuleI(Character, ItemAvoidanceCap), c->GetAccuracy(), RuleI(Character, ItemAccuracyCap),
		c->GetSpellDmg(), RuleI(Character, ItemSpellDmgCap) + NightcapHunt::OutputHeadroom(*c, false),
		c->GetHealAmt(), RuleI(Character, ItemHealAmtCap) + NightcapHunt::OutputHeadroom(*c, true),
		item.DodgeChance + spell.DodgeChance + aa.DodgeChance);
	c->SendPopupToClient("Equipped bonuses and augment stacking", text.c_str());
}

void command_nightcapui(Client *c, const Seperator *sep)
{
	if (sep->argnum == 1 && !strcmp(sep->arg[1], "recommended")) {
		const bool first = c->EnableAARecommendations();
		c->RefreshNightcapUI();
		// A legacy refresh may have just started the throttle. Complete the
		// capability opt-in once; subsequent requests retain the native throttle.
		if (first) { c->SendAlternateAdvancementStats(); }
	} else if (sep->argnum == 1 && !strcmp(sep->arg[1], "refresh")) {
		c->RefreshNightcapUI();
	}
}

void command_nightcappet(Client *c, const Seperator *sep)
{
	c->HandlePetArmor(sep);
}
