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
	int minimum = 0;
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
		"SELECT z.augment_base,z.gear_base,z.min_level,z.night_only FROM nightcap_zone_hunt_zones z "
		"JOIN nightcap_zone_hunt_state s ON s.id=1 AND s.enabled=1 AND s.revision={} "
		"WHERE z.zone_id={} AND z.enabled=1", Revision, content_zone), false);
	if (!config.Success() || config.RowCount() != 1) { return; }
	auto r = config.begin();
	hunt.augment = strtoul(r[0], nullptr, 10); hunt.gear = strtoul(r[1], nullptr, 10);
	hunt.minimum = atoi(r[2]); hunt.night_only = atoi(r[3]) != 0;
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
	hunt.zone_id = z.GetZoneID(); hunt.enabled = !hunt.sources.empty();
	LogInfo("Zone hunt [{}]: [{}] approved native sources", z.GetShortName(), hunt.sources.size());
}

void Award(NPC &npc, bool owned_before_death, bool &rolled)
{
	if (!zone || hunt.zone_id != zone->GetZoneID()) { return; }
	const DeathEligibility e = {hunt.enabled,
		WorldContentService::Instance()->GetCurrentExpansion() == 0, zone->GetInstanceVersion() == 0,
		hunt.sources.count({npc.GetSpawnPointID(), npc.GetNPCTypeID()}) != 0,
		owned_before_death || npc.HasOwner() || npc.IsMerc() || npc.GetSwarmInfo() || npc.GetSwarmOwner(),
		npc.IsQueuedForCorpse(), !hunt.night_only || zone->zone_time.IsNightTime(), npc.GetLevel(), hunt.minimum};
	if (!BeginDeathRoll(rolled, e)) { return; }
	// This path intentionally never calls AddLootTable or the global multiplier.
	for (uint32 base : {hunt.augment, hunt.gear}) {
		if (zone->random.Int(0, 9999) >= FamilyChance) { continue; }
		const uint32 id = base + Quality(zone->random.Int(0, 9999));
		const auto item = database.GetItem(id);
		if (!item) { continue; }
		auto entry = LootdropEntriesRepository::NewNpcEntity();
		entry.item_charges = 1; entry.equip_item = 0;
		npc.AddLootDrop(item, entry, false);
	}
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
