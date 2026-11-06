#include "zone/zone_hunt.h"
#include "zone/client.h"
#include "zone/npc.h"
#include "zone/zone.h"
#include "zone/zonedb.h"
#include "zone/dungeon_service.h"
#include "common/zone_hunt_policy.h"
#include "common/zone_hunt_catalog.h"
#include "common/content/world_content_service.h"
#include <set>
#include <array>

extern Zone *zone;
extern ZoneDatabase database;

namespace NightcapHunt {
namespace {
struct Hunt {
	uint32 zone_id = 0, augment = 0, gear = 0;
	int minimum = 0, augment_chance = 0, gear_chance = 0; // Out of 10000.
	bool enabled = false, night_only = false;
	std::set<std::pair<uint32, uint32>> sources;
} hunt;
}

void Load(Zone &z)
{
	hunt = {};
	if (z.GetInstanceVersion() || WorldContentService::Instance()->GetCurrentExpansion() != 0) { return; }
	const auto content_zone=NightcapDungeon::ContentZone(z.GetZoneID(),NightcapDungeon::Managed());
	auto config = database.QueryDatabase(fmt::format(
		"SELECT z.augment_base,z.gear_base,z.min_level,z.night_only,z.augment_chance,z.gear_chance FROM nightcap_zone_hunt_zones z "
		"JOIN nightcap_zone_hunt_state s ON s.id=1 AND s.enabled=1 AND s.revision={} "
		"WHERE z.zone_id={} AND z.enabled=1", Revision, z.GetZoneID()), false);
	if (!config.Success() || config.RowCount() != 1) { return; }
	auto r = config.begin();
	hunt.augment = strtoul(r[0], nullptr, 10); hunt.gear = strtoul(r[1], nullptr, 10);
	hunt.minimum = atoi(r[2]); hunt.night_only = atoi(r[3]) != 0;
	hunt.augment_chance = atoi(r[4]); hunt.gear_chance = atoi(r[5]); // CHECK constraint bounds both to [0,10000].
	// Actual layout owns its augment. Inherited equipment keeps its own source
	// identity, minimum level, nighttime policy and configured chance.
	if (content_zone != z.GetZoneID()) {
		auto equipment = database.QueryDatabase(fmt::format(
			"SELECT gear_base,min_level,night_only,gear_chance FROM nightcap_zone_hunt_zones "
			"WHERE zone_id={} AND enabled=1", content_zone), false);
		if (!equipment.Success() || equipment.RowCount() != 1) { hunt = {}; return; }
		auto gear = equipment.begin();
		hunt.gear = strtoul(gear[0], nullptr, 10); hunt.minimum = atoi(gear[1]);
		hunt.night_only = atoi(gear[2]) != 0; hunt.gear_chance = atoi(gear[3]);
	}
	if (!IsAugment(hunt.augment) || !NextTier(hunt.gear)) { hunt = {}; return; }
	for (uint32 base : {hunt.augment, hunt.gear}) {
		for (uint32 tier = 0; tier != 4; ++tier) {
			if (!database.GetItem(base + tier)) { hunt = {}; return; }
		}
	}
	auto sources = database.QueryDatabase(fmt::format(
		"SELECT spawn_id,npc_id FROM nightcap_zone_hunt_sources WHERE zone_id={}", content_zone), false);
	if (!sources.Success()) { hunt = {}; return; }
	for (auto row : sources) { hunt.sources.emplace(strtoul(row[0], nullptr, 10), strtoul(row[1], nullptr, 10)); }
	hunt.zone_id = z.GetZoneID(); hunt.enabled = true;
	LogInfo("Zone hunt [{}]: any combat NPC augments; [{}] approved equipment sources", z.GetShortName(), hunt.sources.size());
}

bool CanDropAugment(NPC &npc, bool owned_before_death)
{
	if (!zone) { return false; }
	const bool expedition = NightcapDungeon::Managed() && (zone->GetZoneID() == 760 || zone->GetZoneID() == 113);
	const DeathEligibility e = {(hunt.enabled && hunt.zone_id == zone->GetZoneID()) || expedition,
		WorldContentService::Instance()->GetCurrentExpansion() == 0, zone->GetInstanceVersion() == 0, false,
		owned_before_death || npc.HasOwner() || npc.IsMerc() || npc.GetSwarmInfo() || npc.GetSwarmOwner(),
		npc.IsQueuedForCorpse(), true, npc.GetLevel(), 0};
	return AugmentDeathEligible(e, npc.GetBodyType(),
		npc.GetInvul() || npc.GetSpecialAbility(SpecialAbility::AggroImmunity) ||
		npc.GetSpecialAbility(SpecialAbility::BeingAggroImmunity) ||
		npc.GetSpecialAbility(SpecialAbility::HarmFromClientImmunity));
}

void Award(NPC &npc, bool owned_before_death, bool &rolled)
{
	if (!zone || rolled || hunt.zone_id != zone->GetZoneID()) { return; }
	const DeathEligibility e = {hunt.enabled,
		WorldContentService::Instance()->GetCurrentExpansion() == 0, zone->GetInstanceVersion() == 0,
		hunt.sources.count({npc.GetSpawnPointID(), npc.GetNPCTypeID()}) != 0,
		owned_before_death || npc.HasOwner() || npc.IsMerc() || npc.GetSwarmInfo() || npc.GetSwarmOwner(),
		npc.IsQueuedForCorpse(), !hunt.night_only || zone->zone_time.IsNightTime(), npc.GetLevel(), hunt.minimum};
	const bool augment = CanDropAugment(npc, owned_before_death);
	if (!augment) { return; }
	bool equipment = false;
	BeginDeathRoll(equipment, e);
	if (!augment && !equipment) { return; }
	rolled = true;
	// This path intentionally never calls AddLootTable or the global multiplier.
	for (const auto &[base, chance] : {std::pair{hunt.augment, hunt.augment_chance}, std::pair{hunt.gear, hunt.gear_chance}}) {
		if ((base == hunt.augment && !augment) || (base == hunt.gear && !equipment)) { continue; }
		if (zone->random.Int(0, 9999) >= chance) { continue; }
		const uint32 id = base + Quality(zone->random.Int(0, 9999));
		const auto item = database.GetItem(id);
		if (!item) { continue; }
		auto entry = LootdropEntriesRepository::NewNpcEntity();
		entry.item_charges = 1; entry.equip_item = 0;
		npc.AddLootDrop(item, entry, false);
	}
}

int OutputShieldBlock(Client &c)
{
	const auto shield = c.GetInv().GetItem(14); // Secondary: must be a usable real shield.
	if (!shield || !shield->IsClassCommon() || !c.CanEquipItem(shield->GetItem()) ||
		shield->GetItem()->ItemType != EQ::item::ItemTypeShield ||
		c.GetLevel() < shield->GetItemRequiredLevel(true)) { return 0; }
	int best = 0;
	for (int16 slot : std::array<int16, 6>{2, 7, 12, 17, 18, 19}) {
		const auto parent = c.GetInv().GetItem(slot);
		if (!parent || !parent->IsClassCommon() || !c.CanEquipItem(parent->GetItem()) ||
			c.GetLevel() < parent->GetItemRequiredLevel(true)) { continue; }
		for (uint8 socket = 0; socket < EQ::invaug::SOCKET_COUNT; ++socket) {
			if (parent->GetItem()->AugSlotType[socket] != 22) { continue; }
			const auto aug = parent->GetAugment(socket);
			if (aug && c.CanEquipItem(aug->GetItem()) && c.GetLevel() >= aug->GetItemRequiredLevel(true)) {
				best = std::max(best, AugmentShieldBlock(aug->GetID()));
			}
		}
	}
	return best;
}

int OutputHeadroom(Client &c, bool healing)
{
	if (c.GetLevel() < 50) { return 0; }
	int effective = 0;
	for (int16 slot : std::array<int16, 6>{2, 7, 12, 17, 18, 19}) {
		const auto parent = c.GetInv().GetItem(slot);
		if (!parent || !parent->IsClassCommon() || !c.CanEquipItem(parent->GetItem()) ||
			c.GetLevel() < parent->GetItemRequiredLevel(true)) { continue; }
		const auto recommended = parent->GetItemRecommendedLevel(true);
		for (uint8 socket = 0; socket < EQ::invaug::SOCKET_COUNT; ++socket) {
			if (parent->GetItem()->AugSlotType[socket] != 22) { continue; }
			const auto aug = parent->GetAugment(socket);
			if (!aug || !IsAugment(aug->GetID()) || !c.CanEquipItem(aug->GetItem()) ||
				c.GetLevel() < aug->GetItemRequiredLevel(true)) { continue; }
			const int heroic = healing ? aug->GetItem()->HeroicWis : aug->GetItem()->HeroicInt;
			effective += c.GetLevel() >= recommended ? heroic : c.CalcRecommendedLevelBonus(c.GetLevel(), recommended, heroic);
			break; // One credit-bearing type-22 augment per approved armor location.
		}
	}
	return Headroom(c.GetLevel(), effective);
}
}
