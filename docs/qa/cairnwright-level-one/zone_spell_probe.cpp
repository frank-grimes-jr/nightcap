#include "zone/client.h"
#include "zone/zone.h"
#include "zone/zonedb.h"
#include "zone/zone_config.h"
#include "zone/quest_parser_collection.h"
#include "zone/embparser.h"
#include "zone/npc_scale_manager.h"
#include "zone/map.h"
#include "zone/npc.h"
#include <cstdarg>
#include "common/cairnwright.h"
#include "common/memory_mapped_file.h"
#include "common/path_manager.h"
#include "common/skill_caps.h"
#include "common/zone_store.h"
#include <iostream>
#include <filesystem>
#include <thread>
#include <vector>

extern const ZoneConfig* Config;
extern QuestParserCollection* parse;
extern Zone* zone;
extern NpcScaleManager* npc_scale_manager;


static void check(bool ok, const char* what)
{
	if (!ok) {
		throw std::runtime_error(what);
	}
}

class Subject : public Client {
public:
	std::vector<uint32> fracture_targets;

	void Message(uint32 type, const char* message, ...) override
	{
		va_list args;
		va_start(args, message);
		std::vfprintf(stderr, message, args);
		va_end(args);
		std::fputc('\n', stderr);
	}

	bool SpellOnTarget(uint16 id, Mob* target, int reflect, bool adjust,
		int16 resist, bool proc, int level, int duration, bool disable_overwrite) override
	{
		if (id == Cairnwright::SeamFracture && target) {
			fracture_targets.push_back(target->GetID());
		}
		return Client::SpellOnTarget(id, target, reflect, adjust, resist, proc, level, duration, disable_overwrite);
	}

	void load(const char* name)
	{
		const auto id = database.GetCharacterID(name);
		check(id != 0, "saved character");
		SetCharacterId(id);
		auto &profile = GetPP();
		check(database.LoadCharacterData(id, &profile, &GetEPP()), "load profile");
		SetName(name);
		level = profile.level;
		race = base_race = profile.race;
		class_ = profile.class_;
		deity = profile.deity;
		SetPosition(profile.x, profile.y, profile.z);
		SetHeading(profile.heading);
		SetClientVersion(EQ::versions::ClientVersion::RoF2);
		GetInv().SetInventoryVersion(EQ::versions::ClientVersion::RoF2);
		check(database.LoadCharacterSpellBook(id, &profile), "load spellbook");
		check(database.LoadCharacterMemmedSpells(id, &profile), "load spell gems");
		ReconcileMulticlassSkills();
		CalcBonuses();
		entity_list.AddClient(this);
		SetHP(GetMaxHP());
		SetMana(GetMaxMana());
	}

	void memorize_pair()
	{
		MemSpell(Cairnwright::StrikeCairn, 0);
		MemSpell(Cairnwright::SoundTheSeam, 1);
	}

	void cast(uint16 id, int slot)
	{
		check(HasSpellScribed(id) && GetSpellMinLevel(id) == 1 && GetPP().mem_spells[slot] == id,
			"level one spellbook and gem access");
		const auto initial_mana = GetMana();
		std::cerr << "Casting " << id << " hp=" << GetHP() << " mana=" << initial_mana << std::endl;
		check(CastSpell(id, GetID(), static_cast<EQ::spells::CastingSlot>(slot)), "begin cast");
		for (int elapsed = 0; elapsed < 1700; elapsed += 50) {
			std::this_thread::sleep_for(std::chrono::milliseconds(50));
			Timer::SetCurrentTime();
			SpellProcess();
		}
		check(initial_mana - GetMana() == spells[id].mana, "completed cast mana");
		std::cout << "CAST " << id << " mana=" << initial_mana << "->" << GetMana() << std::endl;
	}

	void plant()
	{
		cast(Cairnwright::StrikeCairn, 0);
		check(EntityVariableExists("cairnwright.stone"), "stone planted");
	}
};

class EncounterNPC : public NPC {
public:
	using NPC::NPC;

	void start_engaged(Subject* player)
	{
		// Start the spell scenario with two engaged enemies, independent of a socket or aggro AI tick.
		hate_list.AddEntToHateList(player, 1);
		check(CheckAggro(player), "fixture starts engaged");
	}
};

static EncounterNPC* spawn(uint32 id, Subject* player, float dx, float dy)
{
	auto* data = content_db.LoadNPCTypesData(id);
	check(data, "NPC content");
	glm::vec4 position(player->GetX() + dx, player->GetY() + dy, player->GetZ(), 0);
	auto* npc = new EncounterNPC(data, nullptr, position, GravityBehavior::Ground);
	entity_list.AddNPC(npc, true, true);
	return npc;
}

static void combat(Subject* player, bool first)
{
	player->load("Cairnproof");
	check(player->GetClass() == 17 && player->GetLevel() == 1 && player->GetMana() >= 9,
		"persisted level one caster");
	if (first) {
		player->memorize_pair();
	}
	player->plant();
	auto* on_line = spawn(2000, player, 4, 0);
	auto* off_line = spawn(2000, player, 4, 12);
	on_line->start_engaged(player);
	off_line->start_engaged(player);
	const auto on_hp = on_line->GetHP();
	const auto off_hp = off_line->GetHP();
	player->SetPosition(player->GetX() + 8, player->GetY(), player->GetZ());
	entity_list.ScanCloseMobs(player);
	player->cast(Cairnwright::SoundTheSeam, 1);
	const auto damage = on_hp - on_line->GetHP();
	std::cout << "DAMAGE on=" << damage << " off=" << off_hp - off_line->GetHP() << std::endl;
	check(player->fracture_targets == std::vector<uint32>{on_line->GetID()}, "only on-line NPC targeted");
	check(damage >= 0 && damage <= 5 && off_line->GetHP() == off_hp, "native magic resist and damage");
}

static void chronicle(Subject* player, const std::string& action, int slot)
{
	player->load(slot == 2 ? "Cairnsecond" : "Cairnthird");
	auto* npc = spawn(999220, player, 1, 0);
	check(parse->HasQuestSub(999220, EVENT_SAY) && parse->HasQuestSub(999220, EVENT_POPUP_RESPONSE),
		"Chronicler bindings");
	if (action == "released") {
		check(!player->IsMulticlassMember(17) && player->GetClass() == 1, "release persisted");
		check(player->GetSpellMinLevel(Cairnwright::StrikeCairn) == 255 &&
			player->GetSpellMinLevel(Cairnwright::SoundTheSeam) == 255, "cast eligibility revoked");
	} else {
		const bool add = action == "adopt";
		check(add || action == "release", "Chronicler action");
		check(player->IsMulticlassMember(17) != add, "starting membership");
		if (!add) {
			player->memorize_pair();
			player->plant();
			player->SetPosition(player->GetX() + 8, player->GetY(), player->GetZ());
			player->cast(Cairnwright::SoundTheSeam, 1);
		}
		const char* choice = add ? "embrace Cairnwright" : (slot == 2 ? "release second" : "release third");
		parse->EventNPC(EVENT_SAY, npc, player, choice, 0);
		parse->EventNPC(EVENT_POPUP_RESPONSE, npc, player, add ? "317" : std::to_string(400 + slot), 0);
		check(player->IsMulticlassMember(17) == add, "Chronicler committed membership");
		if (!add) {
			check(!player->EntityVariableExists("cairnwright.stone"), "release cleared stone");
		}
	}
	if (slot == 3) {
		check(player->GetClass2() == 2, "retained Cleric secondary");
	}
	std::cout << "CHRONICLER " << action << " slot=" << slot << " id=" << player->CharacterID() << std::endl;
}

int main(int argc, char** argv)
{
	check(argc == 2 && std::filesystem::current_path().filename() == "storage-qa", "scratch mode");
	std::string password;
	check(bool(std::getline(std::cin, password)) && !password.empty(), "scratch credential");
	PathManager::Instance()->Init();
	Config = ZoneConfig::get();
	for (auto* db : {&database, &content_db}) {
		check(db->Connect("nightcap-cairnwright-qa-20261121", "cairnwright_qa", password, "cairnwright_qa", 3306),
			"scratch connection");
	}
	ZoneStore::Instance()->LoadZones(content_db);
	const std::string mode = argv[1];
	const bool first = mode == "first";
	if (first) {
		const int count = content_db.GetMaxSpellID() + 1;
		check(count == 44384, "spell IDs");
		EQ::MemoryMappedFile cache("shared/spells", count * sizeof(SPDat_Spell_Struct) + sizeof(uint32));
		cache.ZeroFile();
		content_db.LoadSpells(cache.Get(), count);
	}
	check(database.LoadSpells("", &SPDAT_RECORDS, &spells) && database.LoadItems("") && content_db.LoadItems(""),
		"paired cache");
	SkillCaps::Instance()->SetContentDatabase(&content_db)->LoadSkillCaps();
	Timer::SetCurrentTime();
	npc_scale_manager = new NpcScaleManager;
	zone = new Zone(22, 0, "ecommons");
	check(zone->LoadZoneCFG(zone->GetShortName(), 0), "zone config");
	zone->zonemap = Map::LoadMapFile("ecommons");
	check(zone->zonemap, "East Commonlands geometry");
	zone->LoadBaseData();
	parse = new QuestParserCollection;
	parse->RegisterQuestInterface(new PerlembParser, "pl");
	parse->LoadPerlEventExportSettings(parse->perl_event_export_settings);
	parse->Init();
	for (auto id : {Cairnwright::StrikeCairn, Cairnwright::SoundTheSeam}) {
		check(parse->SpellHasQuestSub(id, EVENT_SPELL_EFFECT_CLIENT), "spell quest hook");
	}
	auto* player = new Subject;
	if (first || mode == "relog") {
		combat(player, first);
	} else {
		check(!mode.empty() && (mode.back() == '2' || mode.back() == '3'), "slot");
		chronicle(player, mode.substr(0, mode.size() - 1), mode.back() - '0');
	}
	std::list<std::string> errors;
	parse->GetErrors(errors);
	for (const auto& error : errors) {
		std::cerr << error << std::endl;
	}
	check(errors.empty(), "Perl quest execution");
	std::cout << "PASS id=" << player->CharacterID() << " mode=" << mode << std::endl;
	std::_Exit(0);
}
