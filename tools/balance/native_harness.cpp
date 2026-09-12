// Diagnostic executable only. Linked separately; never installed as bin/zone.
#include "zone/client.h"
#include "zone/zone.h"
#include "zone/aa_ability.h"
#include "common/json/json.hpp"
#include "common/item_instance.h"
#include "common/rulesys.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

using json = nlohmann::json;
extern Zone *zone;

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
		return true;
	} catch (const std::exception &e) {
		std::cerr << "Balance preflight refused: " << e.what() << std::endl;
		return false;
	}
}

class BalanceClient : public Client {
public:
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
		LoadMulticlassMask(); // Reads only the synthetic row in the isolated database.
		if (GetMulticlassList() != build.at("classes").get<std::vector<uint8>>()) {
			throw std::runtime_error("Synthetic multiclass row does not match input");
		}
		for (const auto &entry : build.at("equipment")) {
			const auto id = entry.at("id").get<uint32>();
			const auto slot = entry.at("slot").get<int16>();
			std::unique_ptr<EQ::ItemInstance> item(database.CreateItem(id));
			if (!item || slot < 1 || slot > 20 || !CanEquipItem(item->GetItem())
				|| !(item->GetItem()->Slots & (uint32(1) << slot))) {
				throw std::runtime_error("Invalid equipped item " + std::to_string(id));
			}
			if (GetInv().PutItem(slot, *item) != slot) {
				throw std::runtime_error("Inventory rejected item " + std::to_string(id));
			}
		}
		CalcBonuses();
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
};

int NightcapBalanceMain(int argc, char **argv)
{
	try {
		EQEmuLogSys::Instance()->SilenceConsoleLogging();
		zone = new Zone(32, 0, "soldungb");
		zone->LoadBaseData();
		zone->LoadAlternateAdvancement();
		std::ifstream input_file(argv[2]);
		json input;
		input_file >> input;
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
			output["builds"].back()["skill_model"] = "Maximum held-class trained caps with native specialization/AA cap rules; attainability requires QA";
			output["builds"].back()["raw_skills"] = std::vector<uint32>(std::begin(c->GetPP().skills),std::end(c->GetPP().skills));
			if (input.value("export_aa_catalog",false)) {
				output["builds"].back()["aa_catalog"] = c->Catalog();
			}
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
