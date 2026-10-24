#include "zone/dungeon_service.h"
#include "common/dungeon_catalog.h"
#include "common/chapterhouse_policy.h"
#include "common/warhelm_policy.h"
#include "common/highkeep_policy.h"
#include "common/faction.h"
#include "common/dungeon_contract.h"
#include "common/content/world_content_service.h"
#include "common/json/json.hpp"
#include "common/say_link.h"
#include "zone/advanced_loot_inventory.h"
#include "zone/advanced_loot_saved_state.h"
#include "zone/client.h"
#include "zone/corpse.h"
#include "zone/groups.h"
#include "zone/npc.h"
#include "zone/task_client_state.h"
#include "zone/zone.h"
#include "zone/spawn2.h"
#include "zone/zonedump.h"
#include <algorithm>
#include <chrono>
#include <ctime>
#include <map>
#include <set>
#include <stdexcept>

extern Zone *zone;
namespace NightcapDungeon {
namespace {
using Json = nlohmann::json;
struct Run {
	std::string id;
	uint16_t instance = 0;
	uint32_t start = 0, owner = 0;
	uint64_t expiry = 0, seed = 0;
	Mode mode = Mode::Grind;
	const Dungeon *dungeon = nullptr;
};
Run current;
bool healthy = true;
std::set<uint32_t> deaths, objectives;
std::map<uint32_t,uint64_t> respawns;
std::map<uint32_t,uint64_t> death_times;
std::map<uint32_t, std::pair<std::string, time_t>> confirmations;
uint64_t Now() { return static_cast<uint64_t>(std::time(nullptr)); }
uint64_t Millis() { return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count(); }
std::string Q(const std::string &s) { return "'" + Strings::Escape(s) + "'"; }
auto Query(const std::string &sql) {
	auto result = database.QueryDatabase(sql, false);
	if (!result.Success()) { throw std::runtime_error("dungeon storage unavailable"); }
	return result;
}
bool StorageReady() {
	// This catalog migration is intentionally single-database. Refuse a split
	// content configuration rather than validate rows the zone does not load.
	const std::string identity="SELECT CONCAT(@@hostname,':',@@port,'/',DATABASE())";
	auto game_identity=Query(identity);
	auto content_identity=content_db.QueryDatabase(identity,false);
	if (!content_identity.Success() || content_identity.RowCount()!=1 || game_identity.RowCount()!=1 ||
		std::string(game_identity.begin()[0])!=content_identity.begin()[0]) { return false; }
	auto limit=Query("SELECT @@group_concat_max_len");
	if (std::stoull(limit.begin()[0])<4096) { return false; }
	const std::string tables="'nightcap_dungeon_state','nightcap_dungeon_runs','nightcap_dungeon_members','nightcap_dungeon_kills',"
		"'nightcap_dungeon_deaths','nightcap_dungeon_loot','nightcap_dungeon_spawns','nightcap_dungeon_checkpoints','nightcap_dungeon_corpses',"
		"'nightcap_dungeon_respawns',"
		"'instance_list','instance_list_player','character_advloot_claims','nightcap_vigil_state','nightcap_vigil_characters'";
	auto engines=Query("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND engine='InnoDB' AND table_name IN ("+tables+")");
	auto triggers=Query("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table IN ("+tables+")");
	if (Strings::ToUnsignedInt(engines.begin()[0])!=15 || Strings::ToUnsignedInt(triggers.begin()[0])!=0) { return false; }
	for (const auto &check : SchemaChecks) {
		auto row=Query(check.sql);
		if (row.RowCount()!=1 || !row.begin()[0] || std::string(row.begin()[0])!=check.expected) {
			LogError("Dungeon schema drift [{}]",check.label); return false;
		}
	}
	return true;
}
bool CatalogReady() {
	for (const auto &check : ContentChecks) {
		auto row=Query(check.sql);
		if (row.RowCount()!=1 || !row.begin()[0] || std::string(row.begin()[0])!=check.expected) {
			LogError("Dungeon content drift [{}]",check.label); return false;
		}
	}
	for (uint32_t id=ItemBegin;id<ItemEnd;++id) {
		const auto item=database.GetItem(id);
		if (!item || !CacheMatches(*item) || !item->NoRent || !item->NoDrop || item->LoreFlag || item->Attuneable || item->Price || item->FixedSellPrice) {
			LogError("Dungeon item cache drift [{}]",id); return false;
		}
	}
	for (uint32_t id:{961000u,961001u,961002u,961003u,961010u,961011u,961012u}) {
		const auto item=database.GetItem(id);
		if (!item || !CacheMatches(*item)) { LogError("Chapterhouse cache drift [{}]",id); return false; }
	}
	return true;
}
struct Transaction {
	bool open = false;
	Transaction() {
		auto status = Query("SELECT @@in_transaction");
		if (status.RowCount()!=1 || std::string(status.begin()[0])!="0") { throw std::runtime_error("nested dungeon transaction"); }
		Query("START TRANSACTION"); open = true;
	}
	void Commit() { Query("COMMIT"); open = false; }
	~Transaction() { if (open) { database.QueryDatabase(std::string("ROLLBACK"), false); } }
};
Run ReadRun(const std::string &where, bool lock = false) {
	auto rows = Query("SELECT r.run_id,r.instance_id,r.instance_start,r.zone_id,r.owner_id,r.mode,r.seed,r.expires_at,r.revision "
		"FROM nightcap_dungeon_runs r JOIN instance_list i ON i.id=r.instance_id AND i.start_time=r.instance_start "
		"AND i.notes=CONCAT('nc-dungeon:',r.run_id) WHERE r.retired=0 AND "+where+(lock ? " FOR UPDATE" : ""));
	if (!rows.RowCount()) { return {}; }
	if (rows.RowCount()!=1) { throw std::runtime_error("ambiguous dungeon run"); }
	auto r=rows.begin(); Run result;
	result.id=r[0]; result.instance=Strings::ToUnsignedInt(r[1]); result.start=Strings::ToUnsignedInt(r[2]);
	result.dungeon=FindDungeon(Strings::ToUnsignedInt(r[3])); result.owner=Strings::ToUnsignedInt(r[4]);
	result.mode=static_cast<Mode>(Strings::ToUnsignedInt(r[5])); result.seed=std::stoull(r[6]); result.expiry=std::stoull(r[7]);
	if (!NightcapLoot::ValidDropID(result.id) || !result.dungeon || !result.dungeon->count ||
		std::stoull(r[8])!=Revision || unsigned(result.mode)>1) { throw std::runtime_error("dungeon catalog mismatch"); }
	return result;
}
Run Personal(uint32_t character, uint32_t destination, bool lock = false) {
	return ReadRun(fmt::format("r.zone_id={} AND r.expires_at>{} AND EXISTS (SELECT 1 FROM nightcap_dungeon_members m WHERE m.run_id=r.run_id AND m.character_id={})",
		destination,Now(),character),lock);
}
const Boss *Objective(uint32_t spawn, uint32_t npc) {
	if (!current.dungeon) { return nullptr; }
	for (const auto &b : Bosses) { if (b.zone==current.dungeon->zone && b.spawn==spawn && b.npc==npc) { return &b; } }
	return nullptr;
}
bool Enabled() {
	auto r=Query(fmt::format("SELECT revision FROM nightcap_dungeon_state WHERE id=1 AND enabled=1 AND revision={}",Revision));
	return r.RowCount()==1 && WorldContentService::Instance()->GetCurrentExpansion()==0;
}
void Enroll(const Run &run, uint32_t character) {
	auto exists=Query(fmt::format("SELECT character_id FROM nightcap_dungeon_members WHERE run_id={} AND character_id={}",Q(run.id),character));
	if (exists.RowCount()) { return; }
	auto count=Query("SELECT COUNT(*) FROM nightcap_dungeon_members WHERE run_id="+Q(run.id));
	if (Strings::ToUnsignedInt(count.begin()[0])>=MaxMembers) { throw std::runtime_error("This run already has six participants."); }
	const auto quality=RollQuality(run.mode,Roll(run.seed,character,2,10000));
	const auto item=SharedItem(run.dungeon->band,Roll(run.seed,character,1,SharedDesigns),quality);
	if (!database.GetItem(item)) { throw std::runtime_error("dungeon item cache incomplete"); }
	Query(fmt::format("INSERT INTO nightcap_dungeon_members(run_id,character_id,reward_item,reward_drop_id) VALUES ({},{},{},{})",
		Q(run.id),character,item,Q(NightcapLoot::NewDropID())));
	Query(fmt::format("INSERT INTO instance_list_player(id,charid) VALUES ({},{})",run.instance,character));
}
std::vector<Client *> Credit(NPC *npc, Mob *killer) {
	std::vector<Client *> result;
	if (!killer) { return result; }
	if (killer->IsNPC() && killer->CastToNPC()->GetSwarmOwner()) { killer=entity_list.GetMobID(killer->CastToNPC()->GetSwarmOwner()); }
	if (killer) { killer=killer->GetUltimateOwner(); }
	if (!killer || !killer->IsClient()) { return result; }
	for (auto c : killer->CastToClient()->GetPartyMembers()) {
		// Same zone process implies same instance. Exact run membership is checked
		// again under the run row lock. Encounter credit is a 200-unit 3D sphere.
		if (c && c->Connected() && c->ClientDataLoaded() &&
			DistanceSquared(c->GetPosition(),npc->GetPosition())<=200.0f*200.0f) { result.push_back(c); }
	}
	return result;
}
void Claim(Client *c, bool automatic=false) {
	if (!StorageReady()) { throw std::runtime_error("dungeon storage contract unavailable"); }
	if (c->IsDead() || (!automatic && (c->IsEngaged() || c->IsCasting())) || c->IsAIControlled() ||
		(c->trade && c->trade->With()) || c->GetTradeskillObject() || c->IsLooting() ||
		c->GetMerchantSessionEntityID() || !c->GetInv().CursorEmpty()) {
		if (!automatic) { c->Message(Chat::Yellow,"Finish combat, close other interactions, and empty your cursor before claiming."); } return;
	}
	auto rows=Query(fmt::format("SELECT m.reward_item,m.reward_drop_id FROM nightcap_dungeon_members m "
		"LEFT JOIN character_advloot_claims c ON c.drop_id=m.reward_drop_id WHERE m.character_id={} "
		"AND m.completed_at>0 AND c.drop_id IS NULL ORDER BY m.completed_at,m.run_id",c->CharacterID()));
	unsigned delivered=0;
	for (auto r=rows.begin(); r!=rows.end(); ++r) {
		const auto id=Strings::ToUnsignedInt(r[0]); const std::string receipt=r[1];
		if (!IsReward(id) || !NightcapLoot::ValidDropID(receipt)) { throw std::runtime_error("invalid dungeon entitlement"); }
		std::unique_ptr<EQ::ItemInstance> item(database.CreateItem(id,1));
		if (!item) { throw std::runtime_error("dungeon item cache incomplete"); }
		const auto result=NightcapLoot::ReceiveItem(c,*item,{receipt});
		if (result==NightcapLoot::TransferResult::Uncertain) { return; }
		if (result!=NightcapLoot::TransferResult::Delivered) {
			c->Message(Chat::Yellow,"Your reward remains available. Make inventory space and choose Claim Rewards again."); return;
		}
		++delivered;
	}
	if (delivered || !automatic) { c->Message(Chat::White,delivered ? "Your earned dungeon rewards have been delivered." : "You have no unclaimed dungeon rewards."); }
}

void JournalHistory(Client *c) {
	if (!c || !c->GetTaskState()) { return; }
	try {
		// History is a repairable display of earned completion, independent of the
		// native instance lifetime and reward delivery. At most fourteen rows.
		auto rows=Query(fmt::format("SELECT r.zone_id,r.mode,MAX(m.completed_at) FROM nightcap_dungeon_members m "
			"JOIN nightcap_dungeon_runs r ON r.run_id=m.run_id WHERE m.character_id={} AND m.completed_at>0 "
			"GROUP BY r.zone_id,r.mode",c->CharacterID()));
		auto state=c->GetTaskState();
		for (auto row : rows) {
			const auto d=FindDungeon(Strings::ToUnsignedInt(row[0]));
			const auto mode=Strings::ToUnsignedInt(row[1]);
			if (!d || mode>1) { continue; }
			const auto task=9700+d->index*2+mode;
			if (!state->RecordCompletedTaskFromLedger(c,task,Strings::ToInt(row[2]))) {
				LogError("Dungeon completed journal remains pending character [{}] zone [{}]",c->CharacterID(),d->zone);
				continue;
			}
			// A failed earlier projection can outlive a reset/expiry. Remove only
			// the display of a completed run, never a newer incomplete run. Native
			// acceptedtime has second precision, so ambiguous same-second runs stay.
			for (int slot=0;slot<MAXACTIVEQUESTS;++slot) {
				if (state->GetActiveTaskID(slot)!=static_cast<int>(task)) { continue; }
				auto matching=Query(fmt::format("SELECT COUNT(CASE WHEN m.completed_at>0 THEN 1 END),"
					"COUNT(CASE WHEN m.completed_at=0 THEN 1 END) FROM nightcap_dungeon_members m "
					"JOIN nightcap_dungeon_runs r ON r.run_id=m.run_id WHERE m.character_id={} "
					"AND r.zone_id={} AND r.mode={} AND r.instance_start={}",c->CharacterID(),d->zone,mode,
					state->GetTaskStartTime(TaskType::Quest,slot)));
				if (matching.RowCount()==1 && Strings::ToUnsignedInt(matching.begin()[0])>0 &&
					Strings::ToUnsignedInt(matching.begin()[1])==0) { state->RemoveTaskByTaskID(c,task); }
				break;
			}
		}
	} catch (const std::exception &e) { LogError("Dungeon history refresh unavailable [{}]",e.what()); }
}

void ShowChecklist(Client *c, const Run &run) {
	auto rows=Query(fmt::format("SELECT boss_id FROM nightcap_dungeon_kills WHERE run_id={} AND character_id={}",Q(run.id),c->CharacterID()));
	std::set<unsigned> done; for (auto r : rows) { done.insert(Strings::ToUnsignedInt(r[0])); }
	const auto now=Now();
	const auto remaining=run.expiry>now ? (run.expiry-now)/60 : 0;
	c->Message(Chat::White,"%s - %s: %u/%u bosses credited, %llu minutes remaining. Open Tasks and select this run for your checklist.",
		run.dungeon->name,run.mode==Mode::Raid ? "Raid" : "Grind",static_cast<unsigned>(done.size()),run.dungeon->count,static_cast<unsigned long long>(remaining));
	for (const auto &b : Bosses) {
		if (b.zone==run.dungeon->zone) { c->Message(Chat::White,"[%s] %s%s",done.count(b.objective) ? "Complete" : "Required",b.name,
			run.mode==Mode::Raid && b.final && !done.count(b.objective) ? " (unlocks after all minibosses)" : ""); }
	}
}
}

#include "zone/chapterhouse_vigil.inc"
#include "zone/warhelm_compact.inc"
#include "zone/highkeep_rescue.inc"
void Process() { Vigil::Tick(); Ashen::Tick(); Highkeep::Tick(); }

void ConfigureJournalTask(int task_id, TaskInformation &task) {
	Vigil::Configure(task_id,task);
	Ashen::Configure(task_id,task);
	if (task_id<9700 || task_id>=9700+static_cast<int>(DungeonCount*2)) { return; }
	const auto &d=Dungeons[(task_id-9700)/2];
	if (task.type!=TaskType::Quest || task.activity_count!=static_cast<int>(d.count+1)) { return; }
	const bool raid=(task_id-9700)%2==1;
	task.description="Defeat every named boss below with personal encounter credit. Open Tasks and select this run to see your checklist. "
		"Task Stage Completed means one boss objective, not the whole dungeon. A full clear appears in Completed history. "
		"Keeper Status shows your permanent counts and remaining time; Claim Rewards delivers any pending item. "
		"No credit is given for missed kills. ";
	task.description+=raid ? "Raid: defeat all minibosses to unlock the final boss. Enemies do not respawn." :
		"Grind: missed bosses can be credited on later respawns.";
	task.reward="One personal completion item per run; pending rewards remain available through the Instance Keeper.";
	for (const auto &b : Bosses) {
		if (b.zone!=d.zone) { continue; }
		auto &activity=task.activity_information[b.objective-1];
		activity.activity_type=TaskActivityType::Kill;
		activity.goal_method=METHODQUEST; // Only the authoritative dungeon ledger may update it.
		activity.target_name=b.name;
		activity.description_override=std::string("Defeat ")+b.name+(raid && b.final ? " (unlocks after all minibosses)" : "");
		activity.step=0; activity.req_activity_id=-1;
	}
	// Retain the installed sentinel so ordinary task updates never dispatch a
	// completion event/reward. The ledger projects completed history directly.
	auto &summary=task.activity_information[d.count];
	summary.activity_type=TaskActivityType::Kill;
	summary.goal_method=METHODQUEST;
	summary.description_override="Full dungeon clear: receive credit for every required boss.";
	if (task_id==9705) {
		task.description+=" New Prison Break runs begin by hailing the Gate Sergeant at the entrance. "
			"Follow the entrance passage to Boshinko, then the prison stairs to Bosec, Dyrna and McCabe. "
			"Hail Osargen in his cell after their defeat. Escort him through three guard waves to the entrance; "
			"stay close and defend him. Keeper Status and zone shouts explain your current objective. "
			"Older runs keep their original four-boss completion rules.";
		summary.description_override="Finish the four-boss clear; new Prison Break runs also require rescuing Osargen.";
	}
	summary.step=1; summary.req_activity_id=-1;
	task.selector_ids.clear();
	for (unsigned i=0;i<d.count;++i) { task.selector_ids.push_back(i); }
}

bool Managed() { return !current.id.empty(); }
std::string RunID() { return current.id; }
bool Boot() {
	Vigil::defense={};
	Ashen::defense={};
	Highkeep::state={};
	current={}; healthy=true; deaths.clear(); objectives.clear(); respawns.clear(); death_times.clear(); confirmations.clear();
	if (!zone || !zone->GetInstanceID() || !FindDungeon(zone->GetZoneID())) { return true; }
	try {
		// Uninstalled feature and legacy native instances retain normal behavior.
		auto native=Query(fmt::format("SELECT notes FROM instance_list WHERE id={}",zone->GetInstanceID()));
		if (native.RowCount()!=1) { return false; }
		const std::string notes=native.begin()[0];
		if (notes.rfind("nc-dungeon:",0)!=0) { return true; }
		if (!StorageReady() || !CatalogReady()) { return false; }
		current=ReadRun(fmt::format("r.instance_id={} AND r.zone_id={}",zone->GetInstanceID(),zone->GetZoneID()));
		if (!Managed() || current.expiry<=Now()) { return false; }
		Highkeep::Boot();
		for (auto r : Query("SELECT spawn_id FROM nightcap_dungeon_deaths WHERE run_id="+Q(current.id))) { deaths.insert(Strings::ToUnsignedInt(r[0])); }
		for (auto r : Query("SELECT boss_id FROM nightcap_dungeon_kills WHERE character_id=0 AND run_id="+Q(current.id))) { objectives.insert(Strings::ToUnsignedInt(r[0])); }
		for (auto r : Query("SELECT spawn_id,respawn_at,died_at FROM nightcap_dungeon_respawns WHERE run_id="+Q(current.id))) {
			respawns[Strings::ToUnsignedInt(r[0])]=std::stoull(r[1]); death_times[Strings::ToUnsignedInt(r[0])]=std::stoull(r[2]);
		}
		LogInfo("Dungeon loaded run [{}] instance [{}] mode [{}] deaths [{}]",current.id,current.instance,unsigned(current.mode),deaths.size());
		return true;
	} catch (const std::exception &e) { healthy=false; LogError("Dungeon boot refused: [{}]",e.what()); return false; }
}
bool RaidNPC(Mob *mob) {
	return Managed() && current.mode==Mode::Raid && mob && mob->IsNPC() && !mob->IsPet() && !mob->HasOwner() &&
		!mob->IsMerc() && !mob->CastToNPC()->GetSwarmOwner() && mob->CastToNPC()->GetSpawnPointID()>0 &&
		mob->GetClass()<=16 && mob->GetNPCTypeID()!=current.dungeon->keeper && mob->GetNPCTypeID()!=SkyKeyService;
}
bool SelectSpawn(uint32_t spawn, uint32_t &npc) {
	if (!Managed()) { return true; }
	if (!healthy || current.expiry<=Now() || (current.mode==Mode::Raid && deaths.count(spawn))) { return false; }
	if (Highkeep::Active() && (spawn==10156 || spawn==10109 || spawn==10210 || spawn==10132)) { return false; }
	if (current.mode==Mode::Grind && RespawnDelay(spawn)>0) { return false; }
	for (const auto &b : Bosses) {
		if (b.zone!=current.dungeon->zone) { continue; }
		if (b.spawn==spawn) {
			if (b.final && current.mode==Mode::Raid && objectives.size()+1<current.dungeon->count) { return false; }
			npc=b.npc; return true;
		}
	}
	// The canonical objective point owns every required NPC, including the final
	// gate. Other random entries cannot bypass it or create duplicate objectives.
	for (const auto &b : Bosses) { if (b.zone==current.dungeon->zone && b.npc==npc) { return false; } }
	for (const auto &excluded : ExcludedNPCs) { if (excluded.zone==current.dungeon->zone && excluded.npc==npc) { return false; } }
	return true;
}
bool RequiredSpawn(uint32_t spawn) {
	if (!Managed()) { return false; }
	for (const auto &b : Bosses) { if (b.zone==current.dungeon->zone && b.spawn==spawn) { return true; } }
	return false;
}
uint32_t RespawnDelay(uint32_t spawn) {
	const auto it=respawns.find(spawn); const auto now=Millis();
	return it==respawns.end() || it->second<=now ? 0 : uint32_t(std::min<uint64_t>(UINT32_MAX,it->second-now));
}
void RestoreTimers(std::unordered_map<uint32_t,uint32_t> &timers) {
	if (!Managed()) { return; }
	timers.clear();
	for (const auto &r : respawns) { timers[r.first]=RespawnDelay(r.first); }
}
void PrivateSpawns(std::vector<Spawn2Repository::Spawn2> &spawns) {
	if (!Managed()) { return; }
	Highkeep::Layout(spawns);
	for (auto &s : spawns) { if (RequiredSpawn(s.id)) { s._condition=0; s.cond_value=0; } }
	const auto private_count=PrivateSpawnCount(current.dungeon->zone);
	if (!private_count) { return; }
	if (current.dungeon->zone==48) {
		spawns.erase(std::remove_if(spawns.begin(),spawns.end(),[](const auto &s) {
			return s.spawngroupID!=999231 && s.spawngroupID!=999240;
		}),spawns.end());
	}
	if (current.dungeon->zone==760 || current.dungeon->zone==113) { spawns.clear(); }
	try {
		auto rows=Query(fmt::format("SELECT spawn_id,group_id,npc_id,x,y,z,heading,respawn,grid_id FROM nightcap_dungeon_spawns WHERE zone_id={}",current.dungeon->zone));
		for (auto r=rows.begin();r!=rows.end();++r) {
			auto s=Spawn2Repository::NewEntity(); s.id=Strings::ToUnsignedInt(r[0]); s.spawngroupID=Strings::ToUnsignedInt(r[1]);
			s.zone=current.dungeon->name; s.version=0; s.x=std::stof(r[3]); s.y=std::stof(r[4]); s.z=std::stof(r[5]); s.heading=std::stof(r[6]);
			s.respawntime=Strings::ToUnsignedInt(r[7]); s.pathgrid=Strings::ToUnsignedInt(r[8]);
			// Saved-state lookup may include the public spawn now hosted elsewhere.
			spawns.erase(std::remove_if(spawns.begin(),spawns.end(),[&](const auto &base) { return base.id==s.id; }),spawns.end());
			spawns.push_back(s);
		}
		if (rows.RowCount()!=private_count) { throw std::runtime_error("Private dungeon population incomplete"); }
		for (const auto &s : spawns) {
			if (!zone->spawn_group_list.GetSpawnGroup(s.spawngroupID)) { content_db.LoadSpawnGroupsByID(s.spawngroupID,&zone->spawn_group_list); }
			if (!zone->spawn_group_list.GetSpawnGroup(s.spawngroupID)) { throw std::runtime_error("Private dungeon spawn group missing"); }
		}
	} catch (...) { healthy=false; spawns.clear(); }
}

bool PrepareLoot(NPC *npc, bool owned) {
	if (!Managed() || npc->IsQueuedForCorpse()) { return true; }
	if (!healthy || current.expiry<=Now()) { return false; }
	if (Highkeep::Active() && npc->GetEntityVariable("highkeep-run")==current.id) {
		npc->ClearLootItems(); npc->SetCopper(0); npc->SetSilver(0); npc->SetGold(0); npc->SetPlatinum(0);
		return true;
	}
	try {
		const auto &run=current;
		// Chapterhouse has no original/global loot. Named relics and the zone
		// augment use per-run, per-spawn, per-life rolls, outside legacy quality
		// upgrades and global multipliers. Corpse receipts persist the result.
		if (run.dungeon->zone==760 && !owned && npc->GetSpawnPointID() && NightcapVigil::Combat(npc->GetNPCTypeID()) &&
			npc->GetEntityVariable("nightcap:vigil-loot").empty()) {
			const auto spawn=npc->GetSpawnPointID();
			const auto seed=Mix(run.seed^death_times[spawn]);
			auto add=[&](uint32_t item) {
				const auto before=npc->GetLootItems().size(); npc->AddItem(item,1,false);
				if (npc->GetLootItems().size()!=before+1) { throw std::runtime_error("Chapterhouse loot materialization failed"); }
			};
			const auto mini=NightcapVigil::MiniReward(npc->GetNPCTypeID());
			if (mini && Roll(seed,spawn,301,10000)<3500) { add(mini); }
			if (Roll(seed,spawn,302,10000)<50) {
				const auto quality=Roll(seed,spawn,303,10000);
				add(NightcapVigil::Augment+(quality<6000 ? 0 : quality<9000 ? 1 : quality<9800 ? 2 : 3));
			}
			npc->SetEntityVariable("nightcap:vigil-loot",run.id);
		}
		if (run.dungeon->zone==113 && !owned && npc->GetSpawnPointID() && NightcapAshen::Combat(npc->GetNPCTypeID()) &&
			npc->GetEntityVariable("nightcap:ashen-loot").empty()) {
			const auto spawn=npc->GetSpawnPointID();
			const auto seed=Mix(run.seed^death_times[spawn]);
			auto add=[&](uint32_t item) {
				const auto before=npc->GetLootItems().size(); npc->AddItem(item,1,false);
				if (npc->GetLootItems().size()!=before+1) { throw std::runtime_error("Kael loot materialization failed"); }
			};
			const auto mini=NightcapAshen::MiniReward(npc->GetNPCTypeID());
			if (mini && Roll(seed,spawn,301,10000)<3500) { add(mini); }
			if (Roll(seed,spawn,302,10000)<50) {
				const auto quality=Roll(seed,spawn,303,10000);
				add(NightcapAshen::Augment+(quality<6000 ? 0 : quality<9000 ? 1 : quality<9800 ? 2 : 3));
			}
			npc->SetEntityVariable("nightcap:ashen-loot",run.id);
		}
		if (current.mode!=Mode::Raid) { return true; }
		const auto boss=Objective(npc->GetSpawnPointID(),npc->GetNPCTypeID());
		if (boss && boss->final && !owned) {
			auto loot=Query("SELECT item_id,drop_id FROM nightcap_dungeon_loot WHERE run_id="+Q(run.id)+" ORDER BY ordinal");
			for (auto r=loot.begin();r!=loot.end();++r) {
				const std::string id=r[1]; bool found=false;
				for (auto i : npc->GetLootItems()) { if (i->advanced_loot_id==id) { found=true; } }
				if (!found) {
				const auto before=npc->GetLootItems().size(); npc->AddItem(Strings::ToUnsignedInt(r[0]),1,false);
				if (npc->GetLootItems().size()!=before+1) { throw std::runtime_error("boss loot materialization failed"); }
				npc->GetLootItems().back()->advanced_loot_id=id;
				}
			}
		}
		return true;
	} catch (const std::exception &e) {
		healthy=false; LogError("Dungeon loot staging failed [{}]",e.what()); return false;
	}
}

bool BeforeDeath(NPC *npc, Mob *killer, bool owned, Corpse *corpse) {
	if (!Managed() || npc->IsQueuedForCorpse()) { return true; }
	if (!npc->GetEntityVariable("nightcap:dungeon-death-committed").empty()) { return false; }
	if (!healthy || current.expiry<=Now()) { return false; }
	if (!Vigil::DynamicDeath(npc,killer,owned) || !Ashen::DynamicDeath(npc,killer,owned)) { return false; }
	if (!Highkeep::Death(npc)) { return false; }
	const auto spawn=npc->GetSpawnPointID();
	if (!spawn) { return true; }
	const auto boss=Objective(spawn,npc->GetNPCTypeID());
	const auto credit=owned ? std::vector<Client *>{} : Credit(npc,killer);
	const auto respawn_at=current.mode==Mode::Grind && npc->GetSpawn() ? Millis()+npc->GetSpawn()->RollDeathRespawnTime() : 0;
	const auto died_at=Millis();
	std::vector<Client *> completed;
	try {
		Transaction tx;
		auto run=ReadRun("r.run_id="+Q(current.id),true);
		if (run.id.empty() || run.expiry<=Now()) { throw std::runtime_error("inactive dungeon death"); }
		if (run.mode==Mode::Raid) {
			auto prior=Query(fmt::format("SELECT spawn_id FROM nightcap_dungeon_deaths WHERE run_id={} AND spawn_id={}",Q(run.id),spawn));
			if (prior.RowCount()) { return false; }
			Query(fmt::format("INSERT INTO nightcap_dungeon_deaths VALUES ({},{})",Q(run.id),spawn));
		} else {
			Query(fmt::format("INSERT INTO nightcap_dungeon_respawns VALUES ({},{},{},{}) ON DUPLICATE KEY UPDATE respawn_at=VALUES(respawn_at),died_at=VALUES(died_at)",Q(run.id),spawn,respawn_at,died_at));
		}
		if (boss && !owned) {
			Query(fmt::format("INSERT IGNORE INTO nightcap_dungeon_kills VALUES ({},0,{})",Q(run.id),boss->objective));
			for (auto c : credit) {
				Query(fmt::format("INSERT IGNORE INTO nightcap_dungeon_kills SELECT run_id,character_id,{} FROM nightcap_dungeon_members WHERE run_id={} AND character_id={}",boss->objective,Q(run.id),c->CharacterID()));
				if (!Highkeep::Active()) {
					auto completion=Query(fmt::format("UPDATE nightcap_dungeon_members m SET completed_at={} WHERE run_id={} AND character_id={} AND completed_at=0 AND "
						"(SELECT COUNT(*) FROM nightcap_dungeon_kills k WHERE k.run_id=m.run_id AND k.character_id=m.character_id)={}",Now(),Q(run.id),c->CharacterID(),run.dungeon->count));
					if (completion.RowsAffected()==1) { completed.push_back(c); }
				}
			}
		}
		if (boss && !owned) { Vigil::Death(run,credit); Ashen::Death(run,credit); }
		if (corpse) {
				Json legacy={{"copper",corpse->GetCopper()},{"silver",corpse->GetSilver()},{"gold",corpse->GetGold()},{"platinum",corpse->GetPlatinum()},{"entries",Json::array()}};
				const auto loot=NightcapLoot::SaveCorpseState(corpse,legacy.dump());
				const auto corpse_id=Json::parse(loot).at("nightcap_advanced_loot_v1").at("coin_id").get<std::string>();
				if (!NightcapLoot::ValidDropID(corpse_id)) { throw std::runtime_error("Invalid finalized corpse identity."); }
				Json envelope={{"npc",npc->GetNPCTypeID()},{"x",corpse->GetX()},{"y",corpse->GetY()},{"z",corpse->GetZ()},{"heading",corpse->GetHeading()},{"loot",loot},{"saved_at",Millis()}};
				const uint64_t decay=Now()+std::max(1u,corpse->GetDecayTime()/1000);
				Query(fmt::format("INSERT INTO nightcap_dungeon_corpses VALUES ({},{},{},{},{})",Q(run.id),spawn,Q(corpse_id),Q(envelope.dump()),decay));
		}
		tx.Commit();
		npc->SetEntityVariable("nightcap:dungeon-death-committed",run.id);
		if (run.mode==Mode::Raid) { deaths.insert(spawn); }
		else { respawns[spawn]=respawn_at; death_times[spawn]=died_at; }
		if (boss && !owned) { objectives.insert(boss->objective); }
		if (boss && !owned) { Highkeep::BossDeath(boss); }
		if (boss) { for (auto c : credit) { Journal(c); if (run.dungeon->zone==760) { Vigil::Project(c); } else if (run.dungeon->zone==113) { Ashen::Project(c); } } }
		for (auto c : completed) {
			c->Message(Chat::Yellow,"Dungeon complete: %s - %s. All %u required bosses credited. Your personal reward is earned. Keeper Status records your permanent completion count.",
				run.dungeon->name,run.mode==Mode::Raid ? "Raid" : "Grind",run.dungeon->count);
			// Eligibility is already committed. Inventory delivery uses its own
			// atomic transaction; failure leaves the immutable Keeper claim intact.
			try { Claim(c,true); } catch (const std::exception &e) { LogError("Dungeon reward remains pending [{}]",e.what()); }
		}
		LogInfo("Dungeon death committed run [{}] spawn [{}] objective [{}]",run.id,spawn,boss ? boss->objective : 0);
		return true;
	} catch (const std::exception &e) {
		// Never retry a possibly committed death in this process. Reboot reads the
		// durable ledger; its complete corpse envelope owns recovery.
		healthy=false; LogError("Dungeon run [{}] suspended after death persistence failure [{}]",current.id,e.what()); return false;
	}
}

void JournalForRun(Client *c, const Run *selected) {
	if (!c || !c->GetTaskState()) { return; }
	try {
		const auto run=selected ? *selected : Managed() ? current : Personal(c->CharacterID(),zone->GetZoneID());
		if (run.id.empty() || run.expiry<=Now()) { return; }
		auto member=Query(fmt::format("SELECT completed_at FROM nightcap_dungeon_members WHERE run_id={} AND character_id={}",Q(run.id),c->CharacterID()));
		if (!member.RowCount()) { return; }
		const auto task=9700+run.dungeon->index*2+unsigned(run.mode);
		auto state=c->GetTaskState();
		const auto completed=Strings::ToInt(member.begin()[0]);
		if (completed>0) {
			if (state->RecordCompletedTaskFromLedger(c,task,completed)) {
				if (state->IsTaskActive(task)) { state->RemoveTaskByTaskID(c,task); }
			} else { LogError("Dungeon completed journal remains pending character [{}]",c->CharacterID()); }
			return;
		}
		const auto key="nightcap:dungeon-journal-"+std::to_string(task);
		if (c->GetEntityVariable(key)!=run.id) {
			bool same_start=false;
			for (int slot=0;slot<MAXACTIVEQUESTS;++slot) {
				if (state->GetActiveTaskID(slot)==static_cast<int>(task) && state->GetTaskStartTime(TaskType::Quest,slot)==static_cast<int>(run.start)) { same_start=true; }
			}
			if (state->IsTaskActive(task) && (!same_start || !c->GetEntityVariable(key).empty())) { state->RemoveTaskByTaskID(c,task); }
			c->SetEntityVariable(key,run.id);
		}
		if (!state->IsTaskActive(task)) { state->AcceptNewTask(c,task,0,run.start); }
		auto rows=Query(fmt::format("SELECT boss_id FROM nightcap_dungeon_kills WHERE run_id={} AND character_id={}",Q(run.id),c->CharacterID()));
		std::set<unsigned> done; for (auto r : rows) { done.insert(Strings::ToUnsignedInt(r[0])); }
		for (unsigned i=1;i<=run.dungeon->count;++i) {
			const auto actual=state->GetTaskActivityDoneCountFromTaskID(task,i-1);
			if (done.count(i) && actual==0) {
				state->UpdateTaskActivity(c,task,i-1,1,true);
				for (const auto &b : Bosses) {
					if (b.zone==run.dungeon->zone && b.objective==i) { c->Message(Chat::Yellow,"Boss credited: %s (%u/%u required bosses). The dungeon is still in progress.",
						b.name,static_cast<unsigned>(done.size()),run.dungeon->count); }
				}
			}
			if (!done.count(i) && actual>0) { state->ResetTaskActivity(c,task,i-1); }
		}
		// Never update the sentinel: native completion hooks are not reward owners.
	} catch (const std::exception &e) { LogError("Dungeon journal unavailable [{}]",e.what()); }
}

void Journal(Client *c) { JournalForRun(c,nullptr); }

void Connected(Client *c) {
	if (!c || !c->Connected() || !zone) { return; }
	if (!database.QueryDatabase(std::string("SELECT id FROM nightcap_dungeon_state WHERE id=1"),false).Success()) {
		if (Managed()) { c->Disconnect(); }
		return;
	}
	try {
		Transaction tx;
		// Only a completed connection acknowledges a transfer. Keeper chat must
		// never clear this reservation while MovePC is still in flight.
		if (Managed()) {
			auto admitted=ReadRun("r.run_id="+Q(current.id),true);
			auto member=Query(fmt::format("SELECT character_id FROM nightcap_dungeon_members WHERE run_id={} AND character_id={}",Q(current.id),c->CharacterID()));
			if (admitted.id.empty() || admitted.expiry<=Now() || !member.RowCount()) {
				tx.Commit(); c->Message(Chat::Yellow,"This dungeon run is no longer available."); c->GoToBind(); return;
			}
		}
		Query(fmt::format("UPDATE nightcap_dungeon_members m JOIN nightcap_dungeon_runs r ON r.run_id=m.run_id SET m.inside_instance=0 "
			"WHERE m.character_id={} AND r.instance_id<>{}",c->CharacterID(),zone->GetInstanceID()));
		if (Managed()) {
			if (current.dungeon->zone==113 && !Ashen::HasJournalRoom(c,9700+current.dungeon->index*2+unsigned(current.mode))) {
				throw std::runtime_error("Make room for the dungeon journal and unfinished Ashen Compact in Tasks.");
			}
			Query(fmt::format("UPDATE nightcap_dungeon_members SET inside_instance=1 WHERE run_id={} AND character_id={}",Q(current.id),c->CharacterID()));
		}
		tx.Commit();
		JournalHistory(c);
		Vigil::Connected(c);
		Ashen::Connected(c);
		if (Managed()) { Journal(c); ShowChecklist(c,current); Highkeep::Status(c); }
	} catch (const std::exception &e) {
		LogError("Dungeon presence update failed [{}]",e.what());
		if (Managed()) { c->Disconnect(); }
	}
}

bool Keeper(Client *c, NPC *keeper, const std::string &action) {
	if (!zone || !keeper) { return false; }
	if (Highkeep::Action(c,keeper,action)) { return true; }
	if (Vigil::Action(c,keeper,action) || Ashen::Action(c,keeper,action)) { return true; }
	const auto d=KeeperDungeon(zone->GetZoneID(),zone->GetInstanceID(),keeper->GetNPCTypeID());
	if (!d) { return keeper->GetNPCTypeID()==998812 || keeper->GetNPCTypeID()==998820 || keeper->GetNPCTypeID()==998860; }
	// False means the Perl legacy implementation may mutate instance_list.
	// Invalid input must be consumed, never translated into legacy permission.
	if (!c || !c->Connected() || !c->ClientDataLoaded()) { return true; }
	if (DistanceSquared(c->GetPosition(),keeper->GetPosition())>50.0f*50.0f) {
		c->Message(Chat::Yellow,"Move closer to the Instance Keeper."); return true;
	}
	try {
		if (d->zone==760 && action!="claim rewards" && (!Vigil::Installed() || c->GetLevel()<50)) {
			throw std::runtime_error("Chapterhouse requires level 50 and an active curated expedition release.");
		}
		if (d->zone==113 && action!="claim rewards" && (!Ashen::Installed() || c->GetLevel()<50)) {
			throw std::runtime_error("Kael requires level 50 and an active Ashen Compact release.");
		}
		// Reject entry before managed or legacy allocation/enrollment can write.
		if ((action=="raid" || action=="grind" || action=="enter" || action=="join" || action=="confirm reset") &&
			!c->CanEnterZone(d->name,0)) {
			c->Message(Chat::Yellow,"You do not meet the entry requirements for %s.",d->name); return true;
		}
		const auto native_id=database.GetInstanceID(d->zone,c->CharacterID(),0);
		bool native_managed=false;
		if (native_id) {
			auto allocation=Query(fmt::format("SELECT notes FROM instance_list WHERE id={}",native_id));
			native_managed=allocation.RowCount()==1 && std::string(allocation.begin()[0]).rfind("nc-dungeon:",0)==0;
		}
		auto table=database.QueryDatabase(std::string("SELECT enabled FROM nightcap_dungeon_state WHERE id=1"),false);
		if (!table.Success() || !table.RowCount()) {
			if (d->zone==760 || d->zone==113) { throw std::runtime_error("Curated campaign storage is unavailable."); }
			if (native_managed || Managed()) { throw std::runtime_error("Managed dungeon storage is unavailable."); }
			auto installed=Query("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='nightcap_dungeon_state'");
			if (std::string(installed.begin()[0])!="0") { throw std::runtime_error("Dungeon feature state is unavailable."); }
			return false;
		}
		const bool enabled=Enabled();
		auto run=Personal(c->CharacterID(),d->zone);
		const bool inspecting=action=="hail" || action.rfind("hail,",0)==0 || action.rfind("hail ",0)==0 || action=="status";
		if (inspecting) { JournalHistory(c); }
		// Existing native allocations retain their original quest flow. Do this
		// before Enter/Join handling, including after feature disablement.
		auto legacy=[&](uint32_t character) {
			const auto id=database.GetInstanceID(d->zone,character,0);
			if (!id) { return false; }
			auto allocation=Query(fmt::format("SELECT notes FROM instance_list WHERE id={}",id));
			return allocation.RowCount()==1 && std::string(allocation.begin()[0]).rfind("nc-dungeon:",0)!=0;
		};
		if (run.id.empty() && action!="claim rewards") {
			if (legacy(c->CharacterID())) {
				if (d->zone==760 || d->zone==113) { throw std::runtime_error("An old curated-zone allocation must expire before a curated run can begin."); }
				return false;
			}
			if (!native_managed && action=="join" && c->GetGroup()) {
				auto leader=Query("SELECT id FROM character_data WHERE name="+Q(c->GetGroup()->GetLeaderName()));
				if (leader.RowCount()==1 && legacy(Strings::ToUnsignedInt(leader.begin()[0]))) {
					if (d->zone==760 || d->zone==113) { throw std::runtime_error("The leader's old curated-zone allocation must expire before a curated run can begin."); }
					return false;
				}
			}
		}
		if (!enabled && run.id.empty() && !native_managed && action!="claim rewards") {
			if (d->zone==760 || d->zone==113) { throw std::runtime_error("New curated dungeon runs are paused."); }
			return false;
		}
		if (action=="claim rewards") { Claim(c); return true; }
		if (native_managed && run.id.empty()) { c->Message(Chat::Yellow,"This managed run has expired or been retired. Earned rewards remain claimable."); return true; }
		if (inspecting) {
			c->Message(Chat::White,"Choose %s or %s for a fresh 12-hour run. %s | %s | %s | %s | %s",
				Saylink::Silent("raid","Raid").c_str(),Saylink::Silent("grind","Grind").c_str(),Saylink::Silent("enter","Enter").c_str(),
				Saylink::Silent("join","Join").c_str(),Saylink::Silent("status","Status").c_str(),Saylink::Silent("claim rewards","Claim Rewards").c_str(),Saylink::Silent("reset","Reset").c_str());
			if (!run.id.empty()) {
				ShowChecklist(c,run);
				Highkeep::Status(c);
				JournalForRun(c,&run);
			}
			auto history=Query(fmt::format("SELECT r.mode,COUNT(*) FROM nightcap_dungeon_members m JOIN nightcap_dungeon_runs r ON r.run_id=m.run_id WHERE m.character_id={} AND m.completed_at>0 AND r.zone_id={} GROUP BY r.mode",c->CharacterID(),d->zone));
			for (auto r : history) { c->Message(Chat::White,"Permanent %s completions: %s",std::string(r[0])=="1" ? "Raid" : "Grind",r[1]); }
			return true;
		}
		if (c->IsDead() || c->IsEngaged() || c->IsCasting() || c->IsAIControlled() || c->IsLooting()) {
			c->Message(Chat::Yellow,"Finish combat and other interactions first."); return true;
		}
		if (action=="reset") {
			if (run.id.empty() || run.owner!=c->CharacterID()) { c->Message(Chat::Yellow,"Only this run's creator can reset it."); return true; }
			confirmations[c->CharacterID()]={run.id,std::time(nullptr)+30};
			c->Message(Chat::Yellow,"Reset this run? Earned claims remain available. %s",Saylink::Silent("confirm reset","Confirm Reset").c_str()); return true;
		}
		if (action=="confirm reset") {
			auto it=confirmations.find(c->CharacterID());
			if (it==confirmations.end() || it->second.first!=run.id || it->second.second<std::time(nullptr)) { c->Message(Chat::Yellow,"Choose Reset again to confirm the current run."); return true; }
			confirmations.erase(it);
			Transaction tx; run=Personal(c->CharacterID(),d->zone,true);
			if (run.id.empty() || run.owner!=c->CharacterID() || zone->GetInstanceID()==run.instance) { throw std::runtime_error("Leave the instance before resetting."); }
			auto busy=Query(fmt::format("SELECT character_id FROM nightcap_dungeon_members WHERE run_id={} AND inside_instance<>0 UNION ALL SELECT charid FROM character_corpses WHERE instance_id={} AND is_buried=0",Q(run.id),run.instance));
			if (busy.RowCount()) { throw std::runtime_error("Players or recoverable player corpses remain inside."); }
			Query("UPDATE nightcap_dungeon_runs SET retired=1 WHERE run_id="+Q(run.id));
			Query(fmt::format("DELETE FROM instance_list_player WHERE id={}",run.instance));
			// Keep the native allocation until its original expiry. It cannot be
			// reused while a dormant/old zone process still has this generation.
			tx.Commit(); c->Message(Chat::White,"Run reset. Choose Raid or Grind to create a new run."); return true;
		}
		if (action=="raid" || action=="grind" || action=="join" || action=="enter") {
			if (zone->GetInstanceID()) { c->Message(Chat::Yellow,"You are already inside an instance."); return true; }
			if (!StorageReady() || !CatalogReady()) { throw std::runtime_error("Dungeon schema, catalog or item cache does not match this release."); }
			const auto destination=GetZoneVersionWithFallback(d->zone,0);
			if (!destination) { throw std::runtime_error("Dungeon destination unavailable."); }
			Transaction tx;
			// Serialize all feature allocations/joins with native allocation state.
			Query("SELECT id FROM nightcap_dungeon_state WHERE id=1 FOR UPDATE");
			run=Personal(c->CharacterID(),d->zone,true);
			if (run.id.empty() && action=="join") {
				auto group=c->GetGroup();
				if (!group) { throw std::runtime_error("Join requires your creator's group."); }
				auto leader=Query("SELECT id FROM character_data WHERE name="+Q(group->GetLeaderName()));
				if (leader.RowCount()!=1) { throw std::runtime_error("Group leader unavailable."); }
				run=Personal(Strings::ToUnsignedInt(leader.begin()[0]),d->zone,true);
				if (run.id.empty()) { throw std::runtime_error("The group leader has no active run."); }
				Enroll(run,c->CharacterID());
			}
			if (run.id.empty()) {
				if (action=="enter") { c->Message(Chat::White,"Choose Raid or Grind to create your run."); return true; }
				if (!enabled || !Enabled() || !d->count) { throw std::runtime_error("New dungeon runs are unavailable."); }
				if (c->GetGroup() && c->GetGroup()->GetLeaderName()!=c->GetName()) { throw std::runtime_error("Your group leader chooses the mode."); }
				auto occupied=Query(fmt::format("SELECT i.id FROM instance_list i JOIN instance_list_player p ON p.id=i.id WHERE p.charid={} AND i.zone={} AND i.version=0 AND (i.never_expires=1 OR i.start_time+i.duration>{})",c->CharacterID(),d->zone,Now()));
				if (occupied.RowCount()) { throw std::runtime_error("An existing native allocation must expire before creating this run."); }
				// The legacy allocator inserts a reservation and may retry a lost
				// connection. Keep selection and insertion inside this no-retry
				// transaction instead; the native primary key arbitrates races.
				const auto reserved=RuleI(Instances,ReservedInstances);
				if (reserved<0 || reserved>=32000) { throw std::runtime_error("Invalid native instance reservation range."); }
				auto free=Query(fmt::format("SELECT MIN(candidate) FROM (SELECT {} AS candidate UNION SELECT id+1 FROM instance_list WHERE id>={}) ids WHERE candidate<=32000 AND NOT EXISTS (SELECT 1 FROM instance_list i WHERE i.id=ids.candidate)",reserved+1,reserved));
				if (!free.RowCount() || !free.begin()[0]) { throw std::runtime_error("No native instance allocation available."); }
				const uint16_t instance=Strings::ToUnsignedInt(free.begin()[0]);
				run.id=NightcapLoot::NewDropID(); run.instance=instance; run.start=Now(); run.expiry=Now()+Duration;
				run.owner=c->CharacterID(); run.mode=action=="raid" ? Mode::Raid : Mode::Grind; run.dungeon=d;
				// A fresh server UUID supplies entropy; only this persisted seed may
				// determine rewards, never time, join order, or client input.
				const auto entropy=NightcapLoot::NewDropID();
				run.seed=0; for (char ch : entropy) { run.seed=Mix(run.seed^static_cast<unsigned char>(ch)); }
				Query(fmt::format("INSERT INTO instance_list(id,zone,version,is_global,start_time,duration,expire_at,never_expires,notes) VALUES ({},{},0,0,{},{},{},0,{})",
					run.instance,d->zone,run.start,Duration,run.expiry,Q("nc-dungeon:"+run.id)));
				Query(fmt::format("INSERT INTO nightcap_dungeon_runs(run_id,instance_id,instance_start,zone_id,owner_id,mode,seed,revision,expires_at) VALUES ({},{},{},{},{},{},{},{},{})",
					Q(run.id),run.instance,run.start,d->zone,run.owner,unsigned(run.mode),run.seed,Revision,run.expiry));
				Highkeep::Create(run);
				Enroll(run,c->CharacterID());
				if (run.mode==Mode::Raid) {
					const auto order=BossOrder(run.seed); const auto count=BossCount(Roll(run.seed,0,3,10000));
					for (unsigned i=0;i<count;++i) {
						const auto item=FinalBossItem(d->index,d->band,order[i],RollQuality(Mode::Raid,Roll(run.seed,0,10+i,10000)));
						if (!database.GetItem(item)) { throw std::runtime_error("dungeon item cache incomplete"); }
						Query(fmt::format("INSERT INTO nightcap_dungeon_loot VALUES ({},{},{},{})",Q(run.id),i,item,Q(NightcapLoot::NewDropID())));
					}
				}
			}
			if (d->zone==760 && !Vigil::HasJournalRoom(c,9700+d->index*2+unsigned(run.mode))) {
				throw std::runtime_error("Make room for both the dungeon journal and any unfinished Vigil quest in Tasks.");
			}
			if (d->zone==113 && !Ashen::HasJournalRoom(c,9700+d->index*2+unsigned(run.mode))) {
				throw std::runtime_error("Make room for the dungeon journal and unfinished Ashen Compact in Tasks.");
			}
			Query(fmt::format("UPDATE nightcap_dungeon_members SET inside_instance=1 WHERE run_id={} AND character_id={}",Q(run.id),c->CharacterID()));
			tx.Commit();
			c->MovePC(d->zone,run.instance,destination->safe_x,destination->safe_y,destination->safe_z,destination->safe_heading); return true;
		}
		return true;
	} catch (const std::exception &e) {
		LogError("Dungeon keeper rejected character [{}]: [{}]",c->CharacterID(),e.what());
		c->Message(Chat::Yellow,"The dungeon operation could not complete: %s",e.what()); return true;
	}
}
}

namespace NightcapDungeon {
namespace {
Json Encode(const SavedSpawn &s) {
	Json j=Json::object();
	j["id"]=s.id;
	j["zone_id"]=s.zone_id;
	j["instance_id"]=s.instance_id;
	j["is_corpse"]=s.is_corpse;
	j["is_zone"]=s.is_zone;
	j["decay_in_seconds"]=s.decay_in_seconds;
	j["npc_id"]=s.npc_id;
	j["spawn2_id"]=s.spawn2_id;
	j["spawngroup_id"]=s.spawngroup_id;
	j["x"]=s.x;
	j["y"]=s.y;
	j["z"]=s.z;
	j["heading"]=s.heading;
	j["respawn_time"]=s.respawn_time;
	j["variance"]=s.variance;
	j["grid"]=s.grid;
	j["current_waypoint"]=s.current_waypoint;
	j["path_when_zone_idle"]=s.path_when_zone_idle;
	j["condition_id"]=s.condition_id;
	j["condition_min_value"]=s.condition_min_value;
	j["enabled"]=s.enabled;
	j["anim"]=s.anim;
	j["loot_data"]=s.loot_data;
	j["entity_variables"]=s.entity_variables;
	j["buffs"]=s.buffs;
	j["hp"]=s.hp;
	j["mana"]=s.mana;
	j["endurance"]=s.endurance;
	j["created_at"]=s.created_at;
	return j;
}
SavedSpawn Decode(const Json &j) {
	auto s=ZoneStateSpawnsRepository::NewEntity();
	j.at("id").get_to(s.id);
	j.at("zone_id").get_to(s.zone_id);
	j.at("instance_id").get_to(s.instance_id);
	j.at("is_corpse").get_to(s.is_corpse);
	j.at("is_zone").get_to(s.is_zone);
	j.at("decay_in_seconds").get_to(s.decay_in_seconds);
	j.at("npc_id").get_to(s.npc_id);
	j.at("spawn2_id").get_to(s.spawn2_id);
	j.at("spawngroup_id").get_to(s.spawngroup_id);
	j.at("x").get_to(s.x);
	j.at("y").get_to(s.y);
	j.at("z").get_to(s.z);
	j.at("heading").get_to(s.heading);
	j.at("respawn_time").get_to(s.respawn_time);
	j.at("variance").get_to(s.variance);
	j.at("grid").get_to(s.grid);
	j.at("current_waypoint").get_to(s.current_waypoint);
	j.at("path_when_zone_idle").get_to(s.path_when_zone_idle);
	j.at("condition_id").get_to(s.condition_id);
	j.at("condition_min_value").get_to(s.condition_min_value);
	j.at("enabled").get_to(s.enabled);
	j.at("anim").get_to(s.anim);
	j.at("loot_data").get_to(s.loot_data);
	j.at("entity_variables").get_to(s.entity_variables);
	j.at("buffs").get_to(s.buffs);
	j.at("hp").get_to(s.hp);
	j.at("mana").get_to(s.mana);
	j.at("endurance").get_to(s.endurance);
	j.at("created_at").get_to(s.created_at);
	return s;
}
std::string Coin(const std::string &loot) {
	const auto j=Json::parse(loot);
	if (j.contains("nightcap_advanced_loot_v1")) { return j.at("nightcap_advanced_loot_v1").at("coin_id").get<std::string>(); }
	return {};
}
std::string AgeRights(const std::string &loot, uint64_t saved_at) {
	auto j=Json::parse(loot);
	if (j.contains("nightcap_advanced_loot_v1")) {
		auto &rights=j["nightcap_advanced_loot_v1"]["rights_delay"];
		const auto remaining=rights.get<uint64_t>(); const auto elapsed=Millis()>saved_at ? Millis()-saved_at : 0;
		rights=remaining>elapsed ? remaining-elapsed : 0;
	}
	return j.dump();
}
}
bool LoadCheckpoint(std::vector<SavedSpawn> &spawns) {
	if (!Managed()) { return false; }
	try {
		spawns.clear();
		auto rows=Query("SELECT payload FROM nightcap_dungeon_checkpoints WHERE run_id="+Q(current.id));
		if (rows.RowCount()) {
			const auto payload=Json::parse(rows.begin()[0]);
			if (!payload.is_array()) { throw std::runtime_error("invalid dungeon checkpoint"); }
			for (const auto &j : payload) {
				auto s=Decode(j);
				if (s.zone_id!=current.dungeon->zone || s.instance_id!=current.instance) { throw std::runtime_error("checkpoint generation mismatch"); }
				if (Highkeep::Active() && !s.is_corpse && !s.is_zone) {
					if (!s.spawn2_id || s.spawn2_id==10156 || s.spawn2_id==10109 || s.spawn2_id==10210 || s.spawn2_id==10132) { continue; }
					const auto p=s.spawn2_id==10145 ? &NightcapHighkeep::Boshinko : s.spawn2_id==10117 ? &NightcapHighkeep::McCabe : nullptr;
					if (p) { s.x=p->x; s.y=p->y; s.z=p->z; s.heading=p->h; s.grid=0; }
				}
				if (s.is_corpse) {
					const auto end=uint64_t(s.created_at)+std::max(0,s.decay_in_seconds);
					if (end<=Now()) { continue; }
					s.decay_in_seconds=end-Now();
					s.loot_data=AgeRights(s.loot_data,uint64_t(s.created_at)*1000);
				} else if (s.spawn2_id && current.mode==Mode::Raid && deaths.count(s.spawn2_id)) { continue; }
				else if (s.spawn2_id && current.mode==Mode::Grind && death_times.count(s.spawn2_id) && death_times.at(s.spawn2_id)>=uint64_t(s.created_at)*1000) { continue; }
				spawns.push_back(s);
			}
		}
		// The transactional death ledger can be newer than a zone checkpoint.
		auto corpses=Query("SELECT corpse_id,payload,expires_at FROM nightcap_dungeon_corpses WHERE run_id="+Q(current.id)+" AND expires_at>"+std::to_string(Now()));
		for (auto row=corpses.begin();row!=corpses.end();++row) {
			const auto payload=Json::parse(row[1]); const auto loot=AgeRights(payload.at("loot").get<std::string>(),payload.at("saved_at").get<uint64_t>());
			const auto coin=Coin(loot);
			if (!NightcapLoot::ValidDropID(coin)) { throw std::runtime_error("invalid recovery coin identity"); }
			bool present=false;
			for (const auto &s : spawns) { if (s.is_corpse && Coin(s.loot_data)==coin) { present=true; break; } }
			if (present) { continue; }
			auto s=ZoneStateSpawnsRepository::NewEntity();
			s.zone_id=current.dungeon->zone; s.instance_id=current.instance; s.is_corpse=1;
			s.npc_id=payload.at("npc").get<uint32_t>(); s.x=payload.at("x").get<float>(); s.y=payload.at("y").get<float>();
			s.z=payload.at("z").get<float>(); s.heading=payload.at("heading").get<float>(); s.loot_data=loot;
			s.decay_in_seconds=std::stoull(row[2])-Now(); s.created_at=Now(); spawns.push_back(s);
		}
	} catch (const std::exception &e) {
		healthy=false; spawns.clear(); LogError("Dungeon checkpoint quarantined run [{}]: [{}]",current.id,e.what());
	}
	return true;
}
bool SaveCheckpoint(const std::vector<SavedSpawn> &spawns) {
	if (!Managed()) { return false; }
	if (!healthy) { return true; } // preserve last known good state after ambiguity
	try {
		Json payload=Json::array();
		for (const auto &s : spawns) { payload.push_back(Encode(s)); }
		Transaction tx;
		Query("SELECT run_id FROM nightcap_dungeon_runs WHERE run_id="+Q(current.id)+" FOR UPDATE");
		Query(fmt::format("INSERT INTO nightcap_dungeon_checkpoints VALUES ({},{},{}) ON DUPLICATE KEY UPDATE payload=VALUES(payload),saved_at=VALUES(saved_at)",Q(current.id),Q(payload.dump()),Now()));
		auto rows=Query("SELECT corpse_id,payload FROM nightcap_dungeon_corpses WHERE run_id="+Q(current.id));
		for (auto row=rows.begin();row!=rows.end();++row) {
			auto corpse=Json::parse(row[1]); const auto coin=Coin(corpse.at("loot").get<std::string>());
			uint64_t expiry=Now();
			for (const auto &s : spawns) {
				if (s.is_corpse && Coin(s.loot_data)==coin) {
					corpse["loot"]=s.loot_data; corpse["saved_at"]=Millis(); expiry=Now()+std::max(0,s.decay_in_seconds); break;
				}
			}
			Query(fmt::format("UPDATE nightcap_dungeon_corpses SET payload={},expires_at=LEAST(expires_at,{}) WHERE run_id={} AND corpse_id={}",Q(corpse.dump()),expiry,Q(current.id),Q(row[0])));
		}
		tx.Commit();
	} catch (const std::exception &e) { healthy=false; LogError("Dungeon checkpoint failed run [{}]: [{}]",current.id,e.what()); }
	return true;
}
}
