#include "zone/client.h"
#include "zone/npc.h"
#include "zone/zonedump.h"
#include "zone/zone.h"
#include "zone/nightcap_sympathetic.h"
#include "common/json/json.hpp"
#include "common/item_instance.h"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <thread>

using json = nlohmann::json;
using EQ::spells::CastingSlot;
extern Zone *zone;

extern "C" unsigned int __wrap__ZNSt13random_device9_M_getvalEv(void *) { return 20261113U; }

bool NightcapBalancePreflight(int argc, char **argv)
{
	if (argc != 4 || std::string(argv[1]) != "tests:balance" ||
		std::filesystem::current_path() != "/tmp/nightcap-sympathetic-local-test-20261113/probe") { return false; }
	std::ifstream f("eqemu_config.json");
	json config; f >> config;
	const auto &s = config.at("server");
	return s.at("database").at("host") == "nightcap-sympathetic-balance" &&
		s.at("database").at("db") == "nightcap_sympathetic_balance" &&
		s.at("database").at("username") == "sympathetic_fixture" &&
		s.at("auto_database_updates") == "false" && !s.contains("content_database");
}

class TestClient : public Client {
public:
	void init(uint8 cls, uint32 id)
	{
		class_ = cls; level = 50; race = base_race = 1; deity = 396;
		auto &p = GetPP(); p.class_ = cls; p.level = level; p.race = race; p.deity = deity;
		p.STR = p.STA = p.AGI = p.DEX = p.INT = p.WIS = p.CHA = 150;
		p.hunger_level = p.thirst_level = 6000;
		std::fill(std::begin(p.InnateSkills), std::end(p.InnateSkills), InnateDisabled);
		std::fill(std::begin(p.skills), std::end(p.skills), 220);
		SetCharacterId(id); SetClientVersion(EQ::versions::ClientVersion::RoF2);
		GetInv().SetInventoryVersion(EQ::versions::ClientVersion::RoF2);
		CalcBonuses();
		entity_list.AddClient(this);
		SetMana(GetMaxMana()); SetHP(GetMaxHP());
	}
	void settle(int ms)
	{
		for (int t = 0; t < ms; t += 50) {
			std::this_thread::sleep_for(std::chrono::milliseconds(50)); Timer::SetCurrentTime(); SpellProcess();
		}
	}
	void equip_damage_stress()
	{
		static EQ::ItemData item{};
		item.ID = 1; item.Slots = 1u << 2; item.Classes = 65535; item.Races = 65535;
		item.ItemType = EQ::item::ItemTypeArmor; item.SpellDmg = 250;
		EQ::ItemInstance instance(&item, 1);
		assert(CanEquipItem(&item) && GetInv().PutItem(2, instance) == 2);
		CalcBonuses();
		assert(GetItemBonuses().SpellDmg == 250);
	}
	void click(uint32 item_id, int slot, uint16 spell)
	{
		settle(1100);
		std::unique_ptr<EQ::ItemInstance> instance(database.CreateItem(item_id));
		assert(instance && instance->GetItem()->Click.Effect == spell);
		assert(CanEquipItem(instance->GetItem()) && GetInv().PutItem(slot, *instance) == slot);
		CalcBonuses();
		assert(CastSpell(spell, GetID(), CastingSlot::Item, instance->GetItem()->CastTime, 0, 0, slot));
		settle(3150);
		assert(FindBuff(spell));
		delete GetInv().PopItem(slot); CalcBonuses(); assert(FindBuff(spell));
	}
	int64 measure(uint16 spell, Mob *target)
	{
		settle(1100);
		GetPP().mem_spells[0] = spell;
		auto hp = target->GetHP();
		std::cerr << "casting " << spell << " target " << target->GetID() << " mana " << GetMana()
			<< " hp " << hp << " level " << int(GetLevel()) << " valid " << IsValidSpell(spell) << std::endl;
		assert(CastSpell(spell,target->GetID(),CastingSlot::Gem1,0,-1));
		return target->GetHP() - hp;
	}
};

int NightcapBalanceMain(int argc, char **argv)
{
	EQEmuLogSys::Instance()->SilenceConsoleLogging();
	auto &settings = EQEmuLogSys::Instance()->log_settings[Logs::Spells];
	settings.log_to_file = 3;
	settings.log_to_console = 3;
	settings.is_category_enabled = 1;
	zone = new Zone(32, 0, "soldungb");
	assert(zone->LoadZoneCFG(zone->GetShortName(), 0) && zone->CanDoCombat());
	zone->LoadBaseData(); zone->LoadAlternateAdvancement();
	assert(RuleI(Expansion, CurrentExpansion) == 0);
	Timer::SetCurrentTime();
	auto *healer = new TestClient(); healer->init(Class::Cleric, 988701);
	healer->SetHP(10);
	auto seed = zone->random;
	auto heal_off = healer->measure(200, healer);
	assert(heal_off > 0);
	healer->click(610150, 15, 44380);
	healer->SetHP(10); zone->random = seed;
	auto heal_on = healer->measure(200, healer);
	assert(heal_on - heal_off == std::min<int64>(48, heal_off / 20) && heal_off / 20 > 0);
	auto *wizard = new TestClient(); wizard->init(Class::Wizard, 988702);
	wizard->equip_damage_stress();
	auto *type = database.LoadNPCTypesData(32040);
	assert(type);
	wizard->SetPosition(-861, -1395, 104.879997f);
	// A high-health practice target avoids dragon level/resist variance in this cap check.
	// The independent encounter matrix measures the unmodified dragons separately.
	auto *practice = new NPCType(*type);
	practice->level = 1; practice->CR = 0; practice->MR = 0;
	auto *victim = new NPC(practice, nullptr, glm::vec4(-871, -1395, 104.879997f, 45), GravityBehavior::Ground);
	entity_list.AddNPC(victim, true, true);
	wizard->SetTarget(victim);
	seed = zone->random;
	auto strike_off = wizard->measure(732, victim);
	std::cerr << "original Ice Comet damage " << -strike_off << std::endl;
	assert(strike_off < 0);
	wizard->click(610338, 5, 44379);
	victim->SetMaxHP(); zone->random = seed;
	auto strike_on = wizard->measure(732, victim);
	std::cerr << "paired deltas " << heal_off << ' ' << heal_on << ' ' << strike_off << ' ' << strike_on << std::endl;
	assert(strike_off - strike_on == std::min<int64>(48, -strike_off / 20) && -strike_off >= 960);
	json evidence = {{"heal_off", heal_off}, {"heal_on", heal_on},
		{"strike_off", -strike_off}, {"strike_on", -strike_on}, {"real_item_casts", 2}};
	std::ofstream out(argv[3]); out << evidence.dump(2);
	return 0;
}
