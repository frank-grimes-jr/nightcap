#include "zone/client.h"
#include "zone/command.h"
#include "common/seperator.h"
#include "common/rulesys.h"
#include "zone/zone_hunt.h"
#include "zone/zone.h"
#include "common/equipped_stats_protocol.h"
#include "common/inventory_stats_protocol.h"
#include "common/spdat.h"
#include "common/nightcap_thj_behaviors.h"

extern Zone *zone;

// Item focus potential only: never evaluate a live cast, roll RNG, consume a
// focus charge or imply that every spell passes its level/cast-time limits.
static void AddEquippedFocus(const EQ::ItemData *item, NightcapStats::Snapshot &s)
{
	if (!item) { return; }
	if (item->Worn.Effect == 3660 && item->Worn.Type == EQ::item::ItemEffectWorn) {
		s.values[NightcapStats::Faerune] = 1;
	}
	if (item->Focus.Type != EQ::item::ItemEffectFocus || !IsValidSpell(item->Focus.Effect)) { return; }
	const auto &focus = spells[item->Focus.Effect];
	for (int i = 0; i < EFFECT_COUNT; ++i) {
		if (focus.effect_id[i] == SpellEffect::IncreaseSpellHaste) {
			s.values[NightcapStats::SpellHaste] = std::max(s.values[NightcapStats::SpellHaste], focus.base_value[i]);
		} else if (focus.effect_id[i] == SpellEffect::ReduceManaCost) {
			const int maximum = RuleB(Spells, UseClassicSpellFocus) || !focus.limit_value[i] ? focus.base_value[i] :
				RuleB(Spells, NightcapTHJBehaviors) ? NightcapTHJ::StrongestEndpoint(focus.base_value[i], focus.limit_value[i]) : focus.limit_value[i];
			if (maximum > s.values[NightcapStats::ManaMax]) {
				s.values[NightcapStats::ManaBase] = focus.base_value[i];
				s.values[NightcapStats::ManaMax] = maximum;
			}
		}
	}
}

static NightcapStats::Snapshot CaptureEquippedStats(Client &c)
{
	using namespace NightcapStats;
	Snapshot s;
	const auto item = c.GetItemBonuses();
	const auto spell = c.GetSpellBonuses();
	const auto aa = c.GetAABonuses();
	s.values[ShieldBlock] = c.HasShieldEquipped() ? item.ShieldBlock + spell.ShieldBlock + aa.ShieldBlock : 0;
	s.values[HuntBlock] = NightcapHunt::OutputShieldBlock(c);
	s.values[Dodge] = item.DodgeChance + spell.DodgeChance + aa.DodgeChance;
	const std::array<int32_t,26> mods = {
		c.GetShielding(), RuleI(Character, ItemShieldingCap), c.GetSpellShield(), RuleI(Character, ItemSpellShieldingCap),
		c.GetDS(), RuleI(Character, ItemDamageShieldCap), c.GetDoTShield(), RuleI(Character, ItemDoTShieldingCap),
		c.GetDSMit(), RuleI(Character, ItemDSMitigationCap), c.GetAvoidance(), RuleI(Character, ItemAvoidanceCap),
		c.GetAccuracy(), RuleI(Character, ItemAccuracyCap), c.GetStunResist(), RuleI(Character, ItemStunResistCap),
		c.GetStrikeThrough(), RuleI(Character, ItemStrikethroughCap),
		c.GetHealAmt(), RuleI(Character, ItemHealAmtCap) + NightcapHunt::OutputHeadroom(c, true),
		c.GetSpellDmg(), RuleI(Character, ItemSpellDmgCap) + NightcapHunt::OutputHeadroom(c, false),
		c.GetClair(), RuleI(Character, ItemClairvoyanceCap), c.GetCombatEffects(), RuleI(Character, ItemCombatEffectsCap)
	};
	for (size_t i = 0; i < mods.size(); ++i) { s.values[Shielding+i] = mods[i]; }
	for (int16 slot = EQ::invslot::EQUIPMENT_BEGIN; slot <= EQ::invslot::EQUIPMENT_END; ++slot) {
		const auto parent = c.GetInv().GetItem(slot);
		if (!parent || !parent->IsClassCommon() || !c.CanEquipItem(parent->GetItem()) ||
			c.GetLevel() < parent->GetItemRequiredLevel(true)) { continue; }
		if (slot == EQ::invslot::slotPowerSource && !(parent->GetItem()->Slots & (uint32{1} << EQ::invslot::slotPowerSource))) { continue; }
		AddEquippedFocus(parent->GetItem(), s);
		for (uint8 socket = 0; socket < EQ::invaug::SOCKET_COUNT; ++socket) {
			const auto aug = parent->GetAugment(socket);
			if (aug && c.CanEquipItem(aug->GetItem()) && c.GetLevel() >= aug->GetItemRequiredLevel(true)) {
				AddEquippedFocus(aug->GetItem(), s);
			}
		}
	}
	return s;
}

static NightcapInventory::Snapshot CaptureInventoryStats(Client &c)
{
	using namespace NightcapInventory;
	Snapshot s;
	// Match the values actually consumed by combat; never recompute cached MIT
	// or substitute item mod2 Avoidance for the complete hit-check defense rating.
	s.values = {
		c.GetMitigationAC(), c.GetTotalDefense(), static_cast<int32_t>(std::min<uint32_t>(c.GetTotalATK(), INT32_MAX)),
		c.GetSpellDmg(), c.GetHealAmt(),
		c.GetSTR(), c.GetSTA(), c.GetAGI(), c.GetDEX(), c.GetWIS(), c.GetINT(), c.GetCHA(),
		c.GetMaxSTR(), c.GetMaxSTA(), c.GetMaxAGI(), c.GetMaxDEX(), c.GetMaxWIS(), c.GetMaxINT(), c.GetMaxCHA(),
		c.GetHeroicSTR(), c.GetHeroicSTA(), c.GetHeroicAGI(), c.GetHeroicDEX(), c.GetHeroicWIS(), c.GetHeroicINT(), c.GetHeroicCHA()
	};
	return s;
}

void Client::RefreshEquippedStats(bool include_inventory)
{
	if (!zone || !m_nightcap_ui_enabled || !m_nightcap_ui_generation || !m_nightcap_ui_refresh_timer.Check(false)) { return; }
	m_nightcap_ui_refresh_timer.Start(3000); // Preserve the existing class-UI throttle.
	auto snapshot = CaptureEquippedStats(*this);
	snapshot.identity = {m_nightcap_ui_generation, CharacterID(), zone->GetZoneID(), zone->GetInstanceID(), GetID()};
	snapshot.sequence = Timer::GetCurrentTime();
	const auto message = NightcapStats::Encode(snapshot);
	if (!message.empty()) { Message(Chat::White, "%s", message.c_str()); }
	if (include_inventory) {
		auto inventory = CaptureInventoryStats(*this);
		inventory.identity = snapshot.identity;
		inventory.sequence = snapshot.sequence;
		const auto frame = NightcapInventory::Encode(inventory);
		if (!frame.empty()) { Message(Chat::White, "%s", frame.c_str()); }
	}
}

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
	if (sep->argnum == 1 && !strcmp(sep->arg[1], "stats")) {
		c->RefreshEquippedStats();
	} else if (sep->argnum == 1 && !strcmp(sep->arg[1], "inventory")) {
		c->RefreshEquippedStats(true);
	} else if (sep->argnum == 1 && !strcmp(sep->arg[1], "recommended")) {
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
