// Diagnostic executable only. Linked separately; never installed as bin/zone.
#include "zone/client.h"
#include "zone/zone.h"
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
		GetInv().SetInventoryVersion(EQ::versions::ClientVersion::RoF2);
		SetCharacterId(build.at("test_character_id").get<uint32>());
		LoadMulticlassMask(); // Reads only the synthetic row in the isolated database.
		if (GetMulticlassList() != build.at("classes").get<std::vector<uint8>>()) {
			throw std::runtime_error("Synthetic multiclass row does not match input");
		}
		for (int skill = 0; skill <= EQ::skills::HIGHEST_SKILL; ++skill) {
			pp.skills[skill] = MaxSkill(static_cast<EQ::skills::SkillType>(skill), class_, level);
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
		json output = { {"status", "Native equipped-stat diagnostic; no purchased AAs or active buffs"},
			{"builds", json::array()} };
		for (const auto &build : input.at("builds")) {
			// Retain test clients until process exit: no disconnect/save/destructor path.
			auto *c = new BalanceClient();
			c->Initialize(build);
			const auto items = c->GetItemBonuses();
			output["builds"].push_back({{"profile", build.at("profile")}, {"tier", build.at("tier")},
				{"hp", c->GetMaxHP()}, {"mana", c->GetMaxMana()}, {"ac_sum", c->ACSum()},
				{"avoidance", c->GetTotalDefense()}, {"str", c->GetSTR()}, {"sta", c->GetSTA()},
				{"agi", c->GetAGI()}, {"dex", c->GetDEX()}, {"int", c->GetINT()}, {"wis", c->GetWIS()},
				{"fr", c->GetFR()}, {"cr", c->GetCR()}, {"mr", c->GetMR()}, {"dr", c->GetDR()}, {"pr", c->GetPR()},
				{"shielding", c->GetShielding()}, {"spellshield", c->GetSpellShield()},
				{"spell_damage", c->GetSpellDmg()}, {"heal_amount", c->GetHealAmt()}, {"haste", c->GetHaste()},
				{"item_hp", items.HP}, {"item_mana", items.Mana},
				{"heroic_hp", items.heroic_max_hp}, {"heroic_mana", items.heroic_max_mana},
				{"item_percent_hp", items.PercentMaxHPChange}, {"item_flat_hp", items.FlatMaxHPChange}});
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
