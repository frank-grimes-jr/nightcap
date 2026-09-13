// Diagnostic executable only. Linked separately; never installed as bin/zone.
#include "zone/client.h"
#include "zone/zone.h"
#include "zone/aa_ability.h"
#include "zone/npc.h"
#include "common/json/json.hpp"
#include "common/item_instance.h"
#include "common/rulesys.h"
#include "common/ptimer.h"
#include "native_runtime.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <atomic>
#include <cstdlib>
#include <map>
#include <tuple>
#include <set>

using json = nlohmann::json;
extern Zone *zone;
static bool profile_save_fixture = false;
uint32 NightcapBalanceAccountId() { return profile_save_fixture ? 1 : 0; }

// Linker wrapping changes only random_device seeding in this executable.
// EQ::Random's native engine and distributions are not replaced or patched.
static std::atomic<uint64_t> balance_seed_calls{0};
extern "C" unsigned int __real__ZNSt13random_device9_M_getvalEv(void *device);
extern "C" unsigned int __wrap__ZNSt13random_device9_M_getvalEv(void *device)
{
	const char *seed = std::getenv("NIGHTCAP_BALANCE_RNG_SEED");
	if (!seed) { return __real__ZNSt13random_device9_M_getvalEv(device); }
	char *end = nullptr;
	const auto value = std::strtoull(seed, &end, 10);
	if (!*seed || *end || *seed == '-' || value > UINT32_MAX) {
		throw std::runtime_error("NIGHTCAP_BALANCE_RNG_SEED must be uint32");
	}
	++balance_seed_calls;
	return static_cast<unsigned int>(value);
}

// Runs before the original main initializes paths, databases, or networking.
bool NightcapBalancePreflight(int argc, char **argv)
{
	try {
		if (argc != 4 || std::string(argv[1]) != "tests:balance") {
			throw std::runtime_error("Expected tests:balance INPUT.json OUTPUT.json");
		}
		auto root = std::filesystem::canonical(std::filesystem::current_path());
		if (root.parent_path() != "/tmp" || root.filename().string().rfind("nightcap-balance-", 0) != 0) {
			throw std::runtime_error("A separate /tmp/nightcap-balance-* runtime is required");
		}
		std::ifstream config_file(root / "eqemu_config.json");
		json config;
		config_file >> config;
		const auto &server = config.at("server");
		const auto &db = server.at("database");
		if (db.at("db") != "nightcap_balance_20260912" || db.at("username") != "nightcap_balance"
			|| server.contains("content_database") || server.at("auto_database_updates") != "false") {
			throw std::runtime_error("Only the isolated balance database/user with updates disabled is allowed");
		}
		for (int i : {2, 3}) {
			auto path = std::filesystem::weakly_canonical(argv[i]);
			if (path.parent_path() != root) {
				throw std::runtime_error("Input and output must be directly inside the isolated runtime");
			}
		}
		std::ifstream fixture_file(argv[2]);
		json fixture;
		fixture_file >> fixture;
		profile_save_fixture = fixture.value("profile_save_fixture", false);
		if (fixture.value("capture_aa_purchase_events", false)) {
			if (!profile_save_fixture) { throw std::runtime_error("Purchase event capture requires an explicit profile fixture"); }
			NightcapBalanceCaptureAAPurchaseEvents();
		}
		if (fixture.value("capture_class_release_transport", false)) {
			if (!profile_save_fixture || !fixture.contains("aa_ownership_probe")) { throw std::runtime_error("Release transport requires an ownership fixture"); }
			NightcapBalanceCaptureReleaseTransport();
		}
		return true;
	} catch (const std::exception &e) {
		std::cerr << "Balance preflight refused: " << e.what() << std::endl;
		return false;
	}
}

class BalanceClient : public Client {
public:
	json CombatState()
	{
		return {{"attack_enabled",attack_timer.Enabled()},{"attack_remaining",attack_timer.GetRemainingTime()},
			{"ranged_enabled",ranged_timer.Enabled()},{"ranged_remaining",ranged_timer.GetRemainingTime()},
			{"melee_disabled",IsMeleeDisabled()},{"target",GetTarget() ? GetTarget()->GetID() : 0},
			{"facing",GetTarget() && IsFacingMob(GetTarget())},{"range",GetTarget() && CombatRange(GetTarget())},
			{"los",GetTarget() && CheckLosFN(GetTarget())},{"heading",GetHeading()}};
	}
	bool Death(Mob *, int64, uint16, EQ::skills::SkillType, KilledByTypes, bool) override
	{ return NightcapBalanceRecordDeath(this); }
	void Damage(Mob *from, int64 damage, uint16 spell, EQ::skills::SkillType skill,
		bool avoidable, int8 slot, bool tick, eSpecialAttacks special) override
	{
		if (!NightcapBalanceIsTerminal(this)) { Client::Damage(from,damage,spell,skill,avoidable,slot,tick,special); }
	}
	void Initialize(const json &build)
	{
		class_ = build.at("classes").at(0).get<uint8>();
		level = build.at("level").get<uint8>();
		race = base_race = 1;
		deity = 396;
		auto &pp = GetPP();
		pp.class_ = class_;
		pp.level = level;
		pp.race = race;
		pp.deity = deity;
		pp.STR = build.at("creation").at("str");
		pp.STA = build.at("creation").at("sta");
		pp.AGI = build.at("creation").at("agi");
		pp.DEX = build.at("creation").at("dex");
		pp.INT = build.at("creation").at("int");
		pp.WIS = build.at("creation").at("wis");
		pp.CHA = build.at("creation").at("cha");
		pp.hunger_level = pp.thirst_level = 6000;
		std::fill(std::begin(pp.InnateSkills), std::end(pp.InnateSkills), InnateDisabled);
		SetClientVersion(EQ::versions::ClientVersion::RoF2);
		pp.expansions = RuleB(World, UseClientBasedExpansionSettings)
			? EQ::expansions::ConvertClientVersionToExpansionsMask(ClientVersion())
			: RuleI(World, ExpansionSettings);
		GetInv().SetInventoryVersion(EQ::versions::ClientVersion::RoF2);
		SetCharacterId(build.at("test_character_id").get<uint32>());
		GetPTimers().SetCharID(CharacterID());
		LoadMulticlassMask(); // Reads only the synthetic row in the isolated database.
		if (GetMulticlassList() != build.at("classes").get<std::vector<uint8>>()) {
			throw std::runtime_error("Synthetic multiclass row does not match input");
		}
		std::set<int16> worn_slots;
		std::set<std::pair<int32,uint32>> lore;
		auto check_lore = [&](const EQ::ItemData *data) {
			if (data->LoreGroup && !lore.insert({data->LoreGroup,data->LoreGroup == -1 ? data->ID : 0}).second) {
				throw std::runtime_error("Equipped item/augment lore conflict");
			}
		};
		for (const auto &entry : build.at("equipment")) {
			const auto id = entry.at("id").get<uint32>();
			const auto slot = entry.at("slot").get<int16>();
			std::unique_ptr<EQ::ItemInstance> item(database.CreateItem(id));
			if (!item || slot < 1 || slot > 20 || !worn_slots.insert(slot).second
				|| item->GetItem()->AugType || item->GetItem()->ReqLevel > GetLevel() || !CanEquipItem(item->GetItem())
				|| !(item->GetItem()->Slots & (uint32(1) << slot))) {
				throw std::runtime_error("Invalid equipped item " + std::to_string(id));
			}
			check_lore(item->GetItem());
			for (const auto &augment : entry.value("augments",json::array())) {
				const int socket = augment.at("socket").get<int>();
				std::unique_ptr<EQ::ItemInstance> aug(database.CreateItem(augment.at("id").get<uint32>()));
				if (!aug || socket < 0 || socket > EQ::invaug::SOCKET_END || !aug->GetItem()->AugType
					|| !CanEquipItem(aug->GetItem()) || aug->GetItem()->ReqLevel > GetLevel()
					|| !(aug->GetItem()->Slots & (uint32(1) << slot))
					|| !item->IsAugmentSlotAvailable(aug->GetItem()->AugType,socket)
					|| IsAugmentRestricted(item->GetItem()->ItemType,aug->GetItem()->AugRestrict)) {
					throw std::runtime_error("Invalid equipped augment/socket");
				}
				check_lore(aug->GetItem());
				item->PutAugment(socket,*aug);
			}
			if (GetInv().PutItem(slot, *item) != slot) {
				throw std::runtime_error("Inventory rejected item " + std::to_string(id));
			}
		}
		CalcBonuses();
	}

	json EquipmentState()
	{
		json result = json::array();
		for (int slot = 1; slot <= 20; ++slot) {
			const auto *item = GetInv().GetItem(slot);
			if (!item) { continue; }
			json augments = json::array();
			for (int socket = 0; socket <= EQ::invaug::SOCKET_END; ++socket) {
				if (const auto *aug = item->GetAugment(socket)) { augments.push_back({{"socket",socket},{"id",aug->GetID()}}); }
			}
			result.push_back({{"slot",slot},{"id",item->GetID()},{"augments",augments},
				{"recommended_level",item->GetItemRecommendedLevel(true)},{"required_level",item->GetItemRequiredLevel(true)}});
		}
		return result;
	}

	json WeaponChecks(const json &ids)
	{
		const auto *type = content_db.LoadNPCTypesData(32040);
		if (!type) { throw std::runtime_error("Missing weapon control NPC"); }
		auto *target = new NPC(type,nullptr,glm::vec4(0,0,0,0),GravityBehavior::Water);
		json result = json::array();
		for (const auto &value : ids) {
			std::unique_ptr<EQ::ItemInstance> item(database.CreateItem(value.get<uint32>()));
			if (!item) { throw std::runtime_error("Invalid weapon control item"); }
			result.push_back({{"id",item->GetID()},{"base_class_equipable",item->IsClassEquipable(GetClass())},
				{"held_class_equipable",CanEquipItem(item->GetItem())},
				{"race_equipable",item->IsRaceEquipable(GetBaseRace())},
				{"required_level",item->GetItemRequiredLevel(true)},
				{"native_weapon_damage",GetWeaponDamage(target,item.get())}});
		}
		return result;
	}

	void ConfigureSkills(const json &build)
	{
		// Explicit trained-skill ceiling. Held-class natural training/client access
		// is a separate QA gate; this is not a claim about a newly created character.
		auto &pp = GetPP();
		const auto primary = build.at("profile") == "war-clr-wiz"
			? EQ::skills::SkillSpecializeEvocation : EQ::skills::SkillSpecializeAlteration;
		const auto secondary = primary == EQ::skills::SkillSpecializeEvocation
			? EQ::skills::SkillSpecializeAlteration : EQ::skills::SkillSpecializeConjuration;
		std::vector<uint16> caps(EQ::skills::HIGHEST_SKILL + 1);
		for (int skill = 0; skill <= EQ::skills::HIGHEST_SKILL; ++skill) {
			for (auto held : GetMulticlassList()) {
				caps[skill] = std::max(caps[skill], MaxSkill(static_cast<EQ::skills::SkillType>(skill), held, level));
			}
			pp.skills[skill] = caps[skill];
			if (skill >= EQ::skills::SkillSpecializeAbjure && skill <= EQ::skills::SkillSpecializeEvocation && skill != primary) {
				pp.skills[skill] = std::min<uint16>(caps[skill], skill == secondary && GetAABonuses().SecondaryForte ? 100 : 50);
			}
		}
		// Resolve all caps against the same valid specialization state before
		// applying cap-raising bonuses; never enter the reset/save path.
		for (int skill = 0; skill <= EQ::skills::HIGHEST_SKILL; ++skill) {
			caps[skill] = GetMaxSkillAfterSpecializationRules(static_cast<EQ::skills::SkillType>(skill), caps[skill]);
		}
		for (int skill = 0; skill <= EQ::skills::HIGHEST_SKILL; ++skill) { pp.skills[skill] = caps[skill]; }
		CalcBonuses();
	}

	json Catalog()
	{
		json result = json::array();
		std::vector<int> ids;
		for (const auto &entry : zone->aa_abilities) { ids.push_back(entry.first); }
		std::sort(ids.begin(), ids.end());
		for (int id : ids) {
			auto *ability = zone->GetAlternateAdvancementAbility(id);
			for (auto *rank = ability->first; rank; rank = rank->next) {
				if (!CanUseAlternateAdvancementRank(rank) || rank->level_req > GetLevel()) { continue; }
				if (rank->cost < 0) { throw std::runtime_error("Negative AA cost requires review"); }
				json effects = json::array(), prereqs = json::array();
				for (const auto &effect : rank->effects) {
					effects.push_back({{"slot",effect.slot},{"effect_id",effect.effect_id},
						{"base",effect.base_value},{"limit",effect.limit_value}});
				}
				for (const auto &prereq : rank->prereqs) {
					prereqs.push_back({{"ability_id",prereq.first},{"ranks",prereq.second},
						{"ability_exists",zone->GetAlternateAdvancementAbility(prereq.first) != nullptr}});
				}
				result.push_back({{"ability_id",id},{"name",ability->name},{"rank_id",rank->id},
					{"rank",rank->current_value},{"cost",rank->cost},{"total_cost",rank->total_cost},
					{"level_req",rank->level_req},{"expansion",rank->expansion},
					{"previous_rank_id",rank->prev_id},{"next_rank_id",rank->next_id},
					{"grant_only",ability->grant_only},{"charges",ability->charges},
					{"category",ability->category},{"type",ability->type},
					{"spell_id",rank->spell},{"cooldown_group",rank->spell_type},
					{"recast_seconds",rank->recast_time},{"effects",effects},{"prereqs",prereqs},
					{"purchasable_now_ignoring_price",CanPurchaseAlternateAdvancementRank(rank,false,true)}});
			}
		}
		return result;
	}

	json Purchase(const json &build)
	{
		const auto budget = build.value("aa_budget",0);
		if (budget < 0) { throw std::runtime_error("Negative AA budget"); }
		GetPP().aapoints = budget;
		json purchases = json::array();
		for (const auto &id : build.value("aa_rank_ids",json::array())) {
			auto *rank = zone->GetAlternateAdvancementRank(id.get<uint32>());
			if (!rank || rank->cost < 0 || !CanPurchaseAlternateAdvancementRank(rank,true,true)) {
				throw std::runtime_error("Native AA purchase gate rejected rank " + id.dump());
			}
			// Same rank mutation and cost as FinishAlternateAdvancementPurchase,
			// after its native purchase gate, excluding UI, quest, title, and event-log side effects.
			if (!SetAA(rank->id,rank->current_value,rank->base_ability->charges)) {
				throw std::runtime_error("Native SetAA rejected rank " + id.dump());
			}
			GetPP().aapoints -= rank->cost;
			GetPP().aapoints_spent += rank->cost;
			purchases.push_back({{"rank_id",rank->id},{"ability_id",rank->base_ability->id},
				{"name",rank->base_ability->name},{"rank",rank->current_value},{"cost",rank->cost},
				{"points_spent",GetSpentAA()}});
		}
		CalcBonuses();
		return purchases;
	}

	template <typename T>
	static bool ReleaseSlotForProbe(T &client, int slot)
	{
		if constexpr (requires { client.ReleaseMulticlassSlot(slot); }) {
			return client.ReleaseMulticlassSlot(slot);
		} else {
			// Reproduce the current Perl plugin's separate class write and native
			// purge on older sources. The same harness selects the atomic entry
			// point when that implementation is available.
			if (slot != 2 && slot != 3) { return false; }
			const uint8 released = slot == 2 ? client.GetClass2() : client.GetClass3();
			if (!released) { return false; }
			if (slot == 2) {
				database.QueryDatabase(fmt::format(
					"UPDATE character_multiclass SET class2=NULLIF(class3,0),class3=NULL WHERE character_id={}", client.CharacterID()));
			} else {
				database.QueryDatabase(fmt::format(
					"UPDATE character_multiclass SET class3=NULL WHERE character_id={}", client.CharacterID()));
			}
			client.PurgeAfterClassRelease(released);
			return true;
		}
	}

	json OwnershipProbe(const json &input)
	{
		if (profile_save_fixture) {
			strn0cpy(GetPP().name, "AA_Lifecycle_Probe", sizeof(GetPP().name));
		}
		if (input.value("load_release_skills", false)) {
			std::fill(std::begin(GetPP().skills), std::end(GetPP().skills), 0);
			auto skills = database.QueryDatabase(fmt::format("SELECT skill_id,value FROM character_skills WHERE id={}", CharacterID()));
			if (!skills.Success()) { throw std::runtime_error("Cannot load release skill fixture"); }
			for (auto row : skills) {
				const auto skill = Strings::ToUnsignedInt(row[0]), value = Strings::ToUnsignedInt(row[1]);
				if (skill > EQ::skills::HIGHEST_SKILL || value > UINT16_MAX) { throw std::runtime_error("Invalid skill fixture"); }
				GetPP().skills[skill] = value;
			}
		}
		const uint32 watched = input.at("first_rank_id");
		const uint32 original_expansions = GetPP().expansions;
		if (input.contains("initial_spent_points")) {
			GetPP().aapoints_spent = input.at("initial_spent_points").get<uint32>();
			GetEPP().expended_aa = input.value("initial_expended_points", uint32(0));
		}
		json steps = json::array();
		for (const auto &operation : input.at("operations")) {
			const auto name = operation.get<std::string>();
			if (input.value("inspect_release_packets", false)) { NightcapBalanceResetReleasePackets(this); }
			bool success = false;
			if (name == "load") { success = database.LoadAlternateAdvancement(this); }
			else if (name == "save") { success = SaveAA(); }
			else if (name == "purchase_first" || name == "purchase_next" || name == "grant" || name == "grant_silent") {
				auto ability = zone->GetAlternateAdvancementAbilityByRank(watched);
				auto rank = ability ? ability->GetRankByPointsSpent(input.value("purchase_rank_count", 1u)) : nullptr;
				if (!rank) { throw std::runtime_error("Unknown acquisition probe rank"); }
				if (name == "purchase_first") { PurchaseAlternateAdvancementRank(watched); success = true; }
				else if (name == "purchase_next") { PurchaseAlternateAdvancementRank(rank->id); success = true; }
				else if (name == "grant") {
					success = GrantAlternateAdvancementAbility(ability->id, input.value("grant_rank_count", 1), input.value("ignore_cost", true));
				} else { FinishAlternateAdvancementPurchase(rank, true, false); success = true; }
			}
			else if (name == "release_second" || name == "release_third" || name == "release_slot") {
				if (!profile_save_fixture) { throw std::runtime_error("Class release requires an explicit profile fixture"); }
				success = ReleaseSlotForProbe(*this, name == "release_slot" ? input.at("release_slot").get<int>() : name == "release_second" ? 2 : 3);
			}
			else if (name == "set_class_slot") {
				SetMulticlassSlot(input.at("set_slot").get<int>(), input.at("set_class").get<int>());
				success = true; // Void setter; persisted/loaded state determines acceptance.
			}
			else if (name == "stale_release_classes") {
				const auto held = input.at("stale_classes").get<std::vector<int>>();
				if (held.size() != 2 || held[0] < 0 || held[0] > 16 || held[1] < 0 || held[1] > 16) { throw std::runtime_error("Invalid stale class fixture"); }
				const auto old2 = GetClass2(), old3 = GetClass3();
				// Load a reviewed synthetic class state, then model an external DB
				// change by restoring storage while the session retains that state.
				auto changed = database.QueryDatabase(fmt::format("UPDATE character_multiclass SET class2={},class3={} WHERE character_id={}", held[0], held[1], CharacterID()), false);
				if (!changed.Success() || changed.RowsAffected() != 1) { throw std::runtime_error("Cannot prepare stale class fixture"); }
				LoadMulticlassMask();
				auto restored = database.QueryDatabase(fmt::format("UPDATE character_multiclass SET class2={},class3={} WHERE character_id={}", old2, old3, CharacterID()), false);
				if (!restored.Success() || restored.RowsAffected() != 1 || GetClass2() != held[0] || GetClass3() != held[1]) { throw std::runtime_error("Cannot restore stale class fixture"); }
				success = true;
			}
			else if (name == "stale_release_skill") {
				const auto skill = input.at("stale_skill").get<int>();
				if (skill < 0 || skill > EQ::skills::HIGHEST_SKILL) { throw std::runtime_error("Invalid stale skill fixture"); }
				GetPP().skills[skill]++;
				success = true;
			}
			else if (name == "refund_all") { RefundAA(); success = true; }
			else if (name == "reset_all") { ResetAA(); success = true; }
			else if (name == "invalidate_earned") { InvalidateEarnedAAState(); success = true; }
			else if (name == "save_character") {
				if (!profile_save_fixture) { throw std::runtime_error("Profile save requires an explicit fixture"); }
				success = database.SaveCharacterData(this, &GetPP(), &GetEPP());
			}
			else if (name == "simulate_committed_reset") {
				if (!profile_save_fixture) { throw std::runtime_error("Commit outcome probe requires an explicit fixture"); }
				auto deleted = database.QueryDatabase(fmt::format(
					"DELETE FROM character_alternate_abilities WHERE id={} AND aa_id={}", CharacterID(), watched));
				auto points = database.QueryDatabase(fmt::format(
					"UPDATE character_data SET aa_points_spent=e_expended_aa_spent WHERE id={}", CharacterID()));
				success = deleted.Success() && points.Success();
			}
			else if (name == "reset_rank" || name == "consume_charge") {
				auto ability = zone->GetAlternateAdvancementAbilityByRank(watched);
				if (!ability) { throw std::runtime_error("Unknown lifecycle ability"); }
				if (name == "reset_rank") { ResetAlternateAdvancementRank(ability->id); }
				else { ExpendAlternateAdvancementCharge(ability->id); }
				success = true; // Void native call completed; observed state decides acceptance.
			}
			else if (name == "restrict_expansions") {
				GetPP().expansions = input.at("expansion_mask").get<uint32>();
				success = true;
			}
			else if (name == "restore_expansions") {
				GetPP().expansions = original_expansions;
				success = true;
			}
			else if (name == "erase_saved") {
				auto deleted = database.QueryDatabase(fmt::format(
					"DELETE FROM character_alternate_abilities WHERE id={} AND aa_id={}", CharacterID(), watched));
				success = deleted.Success();
			} else { throw std::runtime_error("Unknown ownership probe operation"); }
			const auto allowed_failures = input.value("allowed_failures", std::vector<std::string>{});
			if (!success && std::find(allowed_failures.begin(), allowed_failures.end(), name) == allowed_failures.end()) {
				throw std::runtime_error("Native ownership operation failed: " + name);
			}
			const json before_recalculation = {{"spell_crit",GetAABonuses().CriticalSpellChance},{"hp_percent",GetAABonuses().PercentMaxHPChange}};
			CalcBonuses();
			json profile = json::array(), stored = json::array();
			for (const auto &entry : GetPP().aa_array) {
				if (entry.AA || entry.value || entry.charges) {
					profile.push_back({{"first_rank_id",entry.AA},{"rank_count",entry.value},{"charges",entry.charges}});
				}
			}
			auto rows = database.QueryDatabase(fmt::format(
				"SELECT aa_id,aa_value,charges FROM character_alternate_abilities WHERE id={} ORDER BY aa_id", CharacterID()));
			if (!rows.Success()) { throw std::runtime_error("Cannot read ownership probe rows"); }
			for (auto row : rows) {
				stored.push_back({{"first_rank_id",std::stoul(row[0])},{"rank_count",std::stoul(row[1])},{"charges",std::stoul(row[2])}});
			}
			steps.push_back({{"operation",name},{"watched_first_rank_id",watched},{"effective_rank_count",GetAA(watched)},
				{"profile",profile},{"stored",stored},{"unspent_points",GetAAPoints()},{"spent_points",GetSpentAA()},
				{"hp",GetMaxHP()},{"aa_percent_hp",GetAABonuses().PercentMaxHPChange}});
			if (input.value("inspect_earned", false)) {
				auto rank = zone->GetAlternateAdvancementRank(watched);
				steps.back()["success"] = success;
				steps.back()["earned_state_valid"] = HasValidEarnedAAState();
				steps.back()["earned_rank_count"] = GetEarnedAACount(watched);
				steps.back()["first_rank_already_earned"] = rank && HasAlreadyPurchasedRank(rank);
				steps.back()["first_rank_purchasable"] = rank && CanPurchaseAlternateAdvancementRank(rank, true, true);
			}
			if (input.value("inspect_lifecycle", false)) {
				uint32 charges = 0;
				GetAA(watched, &charges);
				steps.back()["active_charges"] = charges;
				steps.back()["expended_points"] = GetEPP().expended_aa;
				auto character = database.QueryDatabase(fmt::format(
					"SELECT aa_points,aa_points_spent,e_expended_aa_spent FROM character_data WHERE id={}", CharacterID()));
				if (!character.Success() || character.RowCount() != 1) { throw std::runtime_error("Lifecycle character fixture missing"); }
				auto row = character.begin();
				steps.back()["saved_points"] = {{"wallet",std::stoul(row[0])},{"spent",std::stoul(row[1])},{"expended",std::stoul(row[2])}};
			}
			if (input.value("inspect_classes", false)) {
				auto classes = database.QueryDatabase(fmt::format(
					"SELECT COALESCE(class2,0),COALESCE(class3,0) FROM character_multiclass WHERE character_id={}", CharacterID()));
				if (!classes.Success() || classes.RowCount() != 1) { throw std::runtime_error("Class release fixture missing"); }
				auto row = classes.begin();
				steps.back()["loaded_classes"] = {GetClass(),GetClass2(),GetClass3()};
				steps.back()["client_data_loaded"] = ClientDataLoaded();
				if (input.value("inspect_release_details", false)) {
					steps.back()["class_mask"] = GetClassMask();
					if (input.value("inspect_release_packets", false)) { steps.back()["release_packets"] = NightcapBalanceReleasePackets(this); }
					steps.back()["connected"] = Connected();
					steps.back()["session_exited"] = !Connected() && !InZone() && !IsLD();
					steps.back()["bonuses_before_recalculation"] = before_recalculation;
					steps.back()["bonuses_after_recalculation"] = {{"spell_crit",GetAABonuses().CriticalSpellChance},{"hp_percent",GetAABonuses().PercentMaxHPChange}};
					steps.back()["loaded_skills"] = json::array();
					for (const auto &skill : input.at("watched_skills")) {
						steps.back()["loaded_skills"].push_back({{"id",skill},{"value",GetRawSkill(static_cast<EQ::skills::SkillType>(skill.get<int>()))}});
					}
					auto skills = database.QueryDatabase(fmt::format("SELECT skill_id,value FROM character_skills WHERE id={} ORDER BY skill_id", CharacterID()));
					if (!skills.Success()) { throw std::runtime_error("Cannot inspect release skills"); }
					steps.back()["saved_skills"] = json::array();
					for (auto skill : skills) {
						steps.back()["saved_skills"].push_back({{"id",Strings::ToUnsignedInt(skill[0])},{"value",Strings::ToUnsignedInt(skill[1])}});
					}
				}
				steps.back()["saved_classes"] = {GetClass(),Strings::ToUnsignedInt(row[0]),Strings::ToUnsignedInt(row[1])};
				auto failures = database.QueryDatabase(std::string("SELECT COALESCE(@nightcap_class_release_failures,0)"));
				if (!failures.Success() || failures.RowCount() != 1) { throw std::runtime_error("Cannot inspect release failure injection"); }
				steps.back()["injected_release_failures"] = Strings::ToUnsignedInt(failures.begin()[0]);
			}
			if (input.value("inspect_purchase_events", false)) {
				steps.back()["purchase_events"] = NightcapBalanceAAPurchaseEvents();
			}
		}
		const std::string scope = input.value("inspect_classes", false)
			? "Native class-release ownership and refund state probe with synthetic rows. No quest interpreter, full session, or skill simulation."
			: "Native AA load/save with synthetic persisted rows and wallet; optional fixture-row deletion models a changed database before reload. No gameplay or refund simulation.";
		return {{"steps",steps},{"scope",scope}};
	}

	json SpellProbes(const json &build, int samples)
	{
		if (!std::getenv("NIGHTCAP_BALANCE_RNG_SEED") || samples < 1 || samples > 100000) {
			throw std::runtime_error("Spell probes require an explicit native seed and 1..100000 samples");
		}
		json result = json::array();
		std::map<uint32, NPC*> targets;
		SetHP(GetMaxHP());
		Mob::SetMana(GetMaxMana()); // Resource state without client UI/update side effects.
		for (const auto &probe : build.at("spell_probes")) {
			const auto spell_id = probe.at("spell_id").get<uint16>();
			if (!IsValidSpell(spell_id)) { throw std::runtime_error("Invalid probe spell"); }
			const auto &spell = spells[spell_id];
			bool eligible = false;
			for (auto held : GetMulticlassList()) {
				eligible |= spell.classes[held - 1] > 0 && spell.classes[held - 1] <= GetLevel();
			}
			// First integration covers one direct CurrentHP effect on a single target.
			// Other effect/target paths must be added explicitly, not silently omitted.
			if (!eligible || spell.effect_id[0] != SpellEffect::CurrentHP || spell.buff_duration != 0
				|| spell.target_type != ST_Target || spell.limit_value[0] != 0) {
				throw std::runtime_error("Unsupported or level-ineligible direct spell probe");
			}
			for (int slot = 1; slot < EFFECT_COUNT; ++slot) {
				if (!IsBlankSpellEffect(spell_id, slot)) { throw std::runtime_error("Multi-effect spell probe requires implementation"); }
			}
			const bool healing = spell.base_value[0] > 0;
			if (healing != (spell.good_effect != 0)) { throw std::runtime_error("Unexpected probe polarity"); }
			Mob *target = this;
			const auto npc_id = probe.value("npc_id",0u);
			if (!healing) {
				if (npc_id != 32040 && npc_id != 73057) { throw std::runtime_error("Expected captured Nagafen/Vox probe target"); }
				if (!targets.count(npc_id)) {
					auto *type = content_db.LoadNPCTypesData(npc_id);
					if (!type) { throw std::runtime_error("Missing native NPC type"); }
					// No EntityList registration, AI loop, loot, movement, or quest events.
					targets[npc_id] = new NPC(type,nullptr,glm::vec4(0,0,0,0),GravityBehavior::Water);
				}
				target = targets.at(npc_id);
			} else if (npc_id) { throw std::runtime_error("Healing probe must target self"); }
			// Each action starts from the same explicit seed. Replay requires the
			// pinned binary/runtime; branch-dependent draw consumption stays native.
			zone->random.Reseed();
			using Outcome = std::tuple<int64,int32,int32,float>;
			std::map<Outcome,int> histogram;
			for (int sample = 0; sample < samples; ++sample) {
				const auto cast_ms = GetActSpellCasttime(spell_id,spell.cast_time);
				float partial = 100;
				if (!healing) {
					partial = target->IsImmuneToSpell(spell_id,this) ? 0
						: target->ResistSpell(spell.resist_type,spell_id,this,true,spell.resist_difficulty);
				}
				int64 amount = 0;
				if (partial > 0) {
					const auto base = target->CalcSpellEffectValue(spell_id,0,GetLevel(),GetInstrumentMod(spell_id),this);
					amount = healing ? GetActSpellHealing(spell_id,base,this)
						: -GetActSpellDamage(spell_id,static_cast<int64>(base*partial/100),target);
				}
				// Normal spell-slot mana cost is resolved after effect application.
				const auto mana = GetActSpellCost(spell_id,spell.mana);
				if (amount < 0 || mana < 0 || cast_ms < 0 || partial < 0 || partial > 100) {
					throw std::runtime_error("Unexpected native spell outcome");
				}
				++histogram[{amount,mana,cast_ms,partial}];
			}
			json outcomes = json::array();
			for (const auto &[value,count] : histogram) {
				outcomes.push_back({{"count",count},{"amount",std::get<0>(value)},
					{"mana",std::get<1>(value)},{"cast_ms",std::get<2>(value)},
					{"landed_percent",std::get<3>(value)}});
			}
			result.push_back({{"spell_id",spell_id},{"name",spell.name},{"effect",healing ? "heal" : "damage"},
				{"caster_hp",GetHP()},{"caster_mana",GetMana()},
				{"npc_id",npc_id},{"target_level",target->GetLevel()},{"target_resist",target->GetResist(spell.resist_type)},
				{"raw_mana",spell.mana},{"raw_cast_ms",spell.cast_time},
				{"raw_recast_ms",spell.recast_time},{"raw_recovery_ms",spell.recovery_time},
				{"specialization",GetSpecializeSkillValue(spell_id)},
				{"samples",samples},{"outcomes",outcomes},
				{"scope","Native direct effect/resist/focus/crit/cost/cast-time samples before Damage/HealDamage; no active buffs or complete casting lifecycle"}});
		}
		return result;
	}
};

json NightcapBalanceClientCombatState(Client *c) { return static_cast<BalanceClient *>(c)->CombatState(); }

int NightcapBalanceMain(int argc, char **argv)
{
	try {
		EQEmuLogSys::Instance()->SilenceConsoleLogging();
		std::ifstream input_file(argv[2]);
		json input;
		input_file >> input;
		const bool runtime = input.value("runtime_probe",false) || input.contains("encounter") || input.contains("aa_probe") || input.contains("pet_probe");
		if (input.contains("aa_ownership_probe") && (runtime || input.at("builds").size() != 1)) {
			throw std::runtime_error("Ownership probe requires one stat-only client");
		}
		if (int(input.value("runtime_probe",false)) + int(input.contains("encounter")) + int(input.contains("aa_probe")) + int(input.contains("pet_probe")) > 1) {
			throw std::runtime_error("Runtime modes require separate processes");
		}
		if (runtime) {
			if (input.at("builds").size() != 1) { throw std::runtime_error("Runtime probe requires one client per process"); }
			if (!std::getenv("NIGHTCAP_BALANCE_RNG_SEED")) { throw std::runtime_error("Runtime requires an explicit RNG seed"); }
			NightcapBalanceStartClock();
		}
		const bool vox = (input.contains("encounter") && input["encounter"].at("npc_id") == 73057)
			|| (input.contains("pet_probe") && input["pet_probe"].contains("combat") && input["pet_probe"]["combat"].at("npc_id") == 73057);
		zone = new Zone(vox ? 73 : 32, 0, vox ? "permafrost" : "soldungb");
		if (runtime && !zone->LoadZoneCFG(zone->GetShortName(),0)) {
			throw std::runtime_error("Cannot load native zone configuration");
		}
		zone->LoadBaseData();
		zone->LoadAlternateAdvancement();
		json output = { {"status", "Native equipped-stat diagnostic; explicitly supplied AA purchases, no active buffs"},
			{"builds", json::array()} };
		for (const auto &build : input.at("builds")) {
			// Retain test clients until process exit: no disconnect/save/destructor path.
			auto *c = new BalanceClient();
			c->Initialize(build);
			const auto purchases = c->Purchase(build);
			c->ConfigureSkills(build);
			const auto items = c->GetItemBonuses();
			const auto aas = c->GetAABonuses();
			output["builds"].push_back({{"profile", build.at("profile")}, {"tier", build.at("tier")},
				{"hp", c->GetMaxHP()}, {"mana", c->GetMaxMana()}, {"ac_sum", c->ACSum()},
				{"avoidance", c->GetTotalDefense()}, {"str", c->GetSTR()}, {"sta", c->GetSTA()},
				{"agi", c->GetAGI()}, {"dex", c->GetDEX()}, {"int", c->GetINT()}, {"wis", c->GetWIS()},
				{"fr", c->GetFR()}, {"cr", c->GetCR()}, {"mr", c->GetMR()}, {"dr", c->GetDR()}, {"pr", c->GetPR()},
				{"shielding", c->GetShielding()}, {"spellshield", c->GetSpellShield()},
				{"spell_damage", c->GetSpellDmg()}, {"heal_amount", c->GetHealAmt()}, {"haste", c->GetHaste()},
				{"item_hp", items.HP}, {"item_mana", items.Mana},
				{"heroic_hp", items.heroic_max_hp}, {"heroic_mana", items.heroic_max_mana},
				{"item_percent_hp", items.PercentMaxHPChange}, {"item_flat_hp", items.FlatMaxHPChange},
				{"aa_percent_hp",aas.PercentMaxHPChange},{"aa_flat_hp",aas.FlatMaxHPChange},
				{"aa_mana",aas.Mana},{"aa_hp_regen",aas.HPRegen},{"aa_mana_regen",aas.ManaRegen},
				{"aa_budget",build.value("aa_budget",0)},{"aa_spent",c->GetSpentAA()},
				{"aa_remaining",c->GetAAPoints()},{"aa_purchases",purchases},
				{"client_expansion_mask",c->GetPP().expansions}});
			if (build.contains("aa_stage")) { output["builds"].back()["aa_stage"] = build["aa_stage"]; }
			if (build.contains("aa_policy")) { output["builds"].back()["aa_policy"] = build["aa_policy"]; }
			if (input.value("export_equipment",false)) { output["builds"].back()["equipped_items"] = c->EquipmentState(); }
			if (input.contains("weapon_check_items")) {
				if (runtime) { throw std::runtime_error("Weapon stat controls require their own process"); }
				output["builds"].back()["weapon_checks"] = c->WeaponChecks(input.at("weapon_check_items"));
			}
			output["builds"].back()["skill_model"] = "Maximum held-class trained caps with native specialization/AA cap rules; attainability requires QA";
			output["builds"].back()["raw_skills"] = std::vector<uint32>(std::begin(c->GetPP().skills),std::end(c->GetPP().skills));
			if (input.value("export_aa_catalog",false)) {
				output["builds"].back()["aa_catalog"] = c->Catalog();
			}
			if (input.contains("aa_ownership_probe")) {
				output["aa_ownership_probe"] = c->OwnershipProbe(input.at("aa_ownership_probe"));
			}
			if (build.contains("spell_probes")) {
				output["builds"].back()["spell_probes"] = c->SpellProbes(build,input.value("spell_samples",1000));
				output["native_rng_seed"] = std::stoull(std::getenv("NIGHTCAP_BALANCE_RNG_SEED"));
				output["native_seed_hook_calls"] = balance_seed_calls.load();
			}
			if (input.value("runtime_probe",false)) {
				output["runtime_probe"] = NightcapBalanceRuntimeProbe(c);
			}
			if (input.contains("aa_probe")) {
				output["aa_probe"] = NightcapBalanceAAProbe(c,input.at("aa_probe"));
				output["status"] = "Native purchased-AA activation diagnostic; cooldowns initially ready";
			}
			if (input.contains("pet_probe")) {
				if (build.at("profile") != "mag-nec-shm" || build.at("classes") != json::array({13,11,10})) {
					throw std::runtime_error("Pet control requires MAG/NEC/SHM");
				}
				output["pet_probe"] = NightcapBalancePetProbe(c,input.at("pet_probe"));
				output["status"] = "Native pet summon/ownership/buff diagnostic; no boss balance claim";
			}
			if (input.contains("encounter")) {
				const auto policy = input.at("encounter").value("combat_policy",std::string("caster_heal"));
				const bool supported = (policy == "caster_heal" && build.at("profile") == "war-clr-wiz")
					|| (policy == "melee_heal" && build.at("profile") == "war-clr-mnk"
						&& build.at("classes") == json::array({1,2,7}));
				if (!supported || input.value("runtime_probe",false)) {
					throw std::runtime_error("Encounter policy does not match its supported class profile");
				}
				output["encounter"] = NightcapBalanceEncounter(c,input.at("encounter"));
				if (input.at("encounter").contains("active_aa_policy")) {
					output["status"] = "Native encounter diagnostic with explicit purchased-AA activation policy";
				}
			}
			if (runtime) { output["native_rng_seed"] = std::stoull(std::getenv("NIGHTCAP_BALANCE_RNG_SEED")); }
		}
		std::ofstream output_file(argv[3]);
		output_file << output.dump(2) << std::endl;
		if (!output_file) { throw std::runtime_error("Failed to write report"); }
		return 0;
	} catch (const std::exception &e) {
		std::cerr << "Native balance failed: " << e.what() << std::endl;
		return 1;
	}
}
