// Compiled by titles.cpp: no new translation unit or Client layout change.
#include "common/earned_title_policy.h"
#include "common/dungeon_catalog.h"
#include "zone/dungeon_service.h"
#include "zone/npc.h"
#include "zone/zone.h"
#include <set>
#include <stdexcept>

extern Zone *zone;
namespace NightcapTitles {
namespace {
auto Query(const std::string &sql) {
	auto rows=database.QueryDatabase(sql,false);
	if (!rows.Success()) { throw std::runtime_error("earned-title storage unavailable"); }
	return rows;
}
bool Enabled() {
	for (const auto &t : title_manager.GetTitles()) {
		if (t.id>=TitleBegin && t.id<TitleEnd) { throw std::runtime_error("reserved earned-title ID collision"); }
	}
	auto rows=Query("SELECT enabled FROM nightcap_title_settings WHERE id=1 AND catalog_version=1");
	return rows.RowCount()==1 && rows.begin()[0] && std::string(rows.begin()[0])=="1";
}
bool Player(Client *c) { return c && c->Admin()==0 && !c->GetGM() && c->Connected() && c->ClientDataLoaded(); }
unsigned SkillCap(Client *c, unsigned skill) {
	unsigned cap=0;
	for (auto cls : c->GetMulticlassList()) {
		cap=std::max(cap,static_cast<unsigned>(c->MaxSkill(static_cast<EQ::skills::SkillType>(skill),cls,50)));
	}
	return cap;
}
std::set<unsigned> Awards(Client *c) {
	std::set<unsigned> awards;
	for (auto row : Query(fmt::format("SELECT title_id FROM nightcap_title_awards WHERE character_id={}",c->CharacterID()))) {
		awards.insert(Strings::ToUnsignedInt(row[0]));
	}
	return awards;
}
void Grant(Client *c, const Definition &d) {
	auto rows=Query(fmt::format("INSERT IGNORE INTO nightcap_title_awards(character_id,title_id,earned_at) VALUES ({},{},UNIX_TIMESTAMP())",c->CharacterID(),d.id));
	if (rows.RowsAffected()==1) { c->Message(Chat::Yellow,"Title earned: %s. Select it in the Titles window.",d.name); }
}
Snapshot Read(Client *c) {
	Snapshot s;
	s.level=c->GetLevel();
	std::map<unsigned,unsigned> saved_skills;
	for (auto row : Query(fmt::format("SELECT skill_id,value FROM character_skills WHERE id={}",c->CharacterID()))) {
		saved_skills[Strings::ToUnsignedInt(row[0])]=Strings::ToUnsignedInt(row[1]);
	}
	for (auto row : Query(fmt::format("SELECT counter_id,value FROM nightcap_title_counters WHERE character_id={}",c->CharacterID()))) {
		s.counters[Strings::ToUnsignedInt(row[0])]=std::stoull(row[1]);
	}
	for (const auto &d : Catalog) {
		if (d.kind==Kind::Skill) {
			s.skills[d.key]={std::min(saved_skills[d.key],c->GetRawSkill(static_cast<EQ::skills::SkillType>(d.key))),SkillCap(c,d.key)};
		}
	}
	// Durable, per-member full completion; enrollment, global boss kills and
	// completing a final boss alone cannot substitute for personal full credit.
	for (auto row : Query(fmt::format("SELECT DISTINCT r.zone_id,r.mode FROM nightcap_dungeon_members m JOIN nightcap_dungeon_runs r ON r.run_id=m.run_id WHERE m.character_id={} AND m.completed_at>0",c->CharacterID()))) {
		const auto z=NormalizeZone(Strings::ToUnsignedInt(row[0]));
		s.clear_zones.insert(z);
		if (std::string(row[1])=="1") { s.raid_zones.insert(z); }
	}
	// Historical named victories may be recovered from personal boss credit,
	// including Grind. General slayer totals cannot be reconstructed from it.
	for (auto row : Query(fmt::format("SELECT DISTINCT r.zone_id,k.boss_id FROM nightcap_dungeon_kills k JOIN nightcap_dungeon_runs r ON r.run_id=k.run_id WHERE k.character_id={} AND k.character_id>0 AND r.zone_id IN (32,73,72)",c->CharacterID()))) {
		const auto z=Strings::ToUnsignedInt(row[0]), objective=Strings::ToUnsignedInt(row[1]);
		if (z==32 && objective==13) { s.counters[100]=std::max(uint64_t(1),Counter(s,100)); }
		if (z==73 && objective==8) { s.counters[101]=std::max(uint64_t(1),Counter(s,101)); }
		if (z==72 && objective==4) { s.counters[102]=std::max(uint64_t(1),Counter(s,102)); }
	}
	for (auto row : Query(fmt::format("SELECT DISTINCT taskid FROM completed_tasks WHERE charid={} AND taskid=9515 AND activityid=-1",c->CharacterID()))) {
		s.tasks.insert(Strings::ToUnsignedInt(row[0]));
	}
	return s;
}
void Refresh(Client *c, const Snapshot &s, std::set<unsigned> &awards) {
	if (!Player(c)) { return; }
	for (const auto &d : Catalog) {
		if (!awards.count(d.id) && Earned(d,s)) { Grant(c,d); awards.insert(d.id); }
	}
}
}
std::string Name(unsigned id, bool suffix) {
	const auto d=Find(id);
	return d && d->suffix==suffix ? d->name : "";
}
void AppendEligible(Client *c, const std::vector<TitlesRepository::Titles> &, std::vector<TitlesRepository::Titles> &out) {
	try {
		if (!c || !Enabled()) { return; }
		auto awards=Awards(c);
		const auto s=Read(c);
		Refresh(c,s,awards);
		for (const auto &d : Catalog) {
			if (!awards.count(d.id)) { continue; }
			auto t=TitlesRepository::NewEntity();
			t.id=d.id;
			if (d.suffix) { t.suffix=d.name; } else { t.prefix=d.name; }
			out.push_back(t);
		}
	} catch (const std::exception &e) { LogError("Earned title list unavailable [{}]",e.what()); }
}
void RecordKill(NPC *npc, Client *credit, bool excluded) {
	// This runs after the native death/corpse commitment, never on a death veto.
	if (!npc || !credit || excluded || !npc->GetSpawnPointID() || NightcapDungeon::Campaign() ||
		NightcapDungeon::HighkeepTransient(npc) || !npc->GetEntityVariable("nightcap:title-death").empty()) { return; }
	npc->SetEntityVariable("nightcap:title-death","1");
	try {
		if (!Enabled()) { return; }
		const auto keys=KillKeys(npc->GetBodyType(),zone->GetZoneID(),npc->GetNPCTypeID());
		std::set<unsigned> seen;
		for (auto c : credit->GetPartyMembers()) {
			if (!c || !seen.insert(c->CharacterID()).second || !CreditEligible(Player(c),c->ClientDataLoaded(),
				!c->IsDead() && c->GetHP()>0,c->GetLevelCon(npc->GetLevel())!=ConsiderColor::Gray,true,
				DistanceSquared(c->GetPosition(),npc->GetPosition()))) { continue; }
			std::string values;
			for (auto key : keys) { values+=fmt::format("{}({},{},1)",values.empty() ? "" : ",",c->CharacterID(),key); }
			// One atomic multi-row statement per participant. Counters saturate at
			// 10,000, the highest required total. Never replay an uncertain write.
			Query("INSERT INTO nightcap_title_counters(character_id,counter_id,value) VALUES "+values+
				" ON DUPLICATE KEY UPDATE value=LEAST(value+1,10000)");
			Snapshot s;
			for (auto row : Query(fmt::format("SELECT counter_id,value FROM nightcap_title_counters WHERE character_id={}",c->CharacterID()))) {
				s.counters[Strings::ToUnsignedInt(row[0])]=std::stoull(row[1]);
			}
			auto awards=Awards(c);
			Refresh(c,s,awards);
		}
	} catch (const std::exception &e) { LogError("Earned title kill credit failed; no replay [{}]",e.what()); }
}
void CheckSkill(Client *c, unsigned skill) {
	if (!Player(c) || c->GetLevel()<50) { return; }
	bool tracked=false;
	for (const auto &d : Catalog) { if (d.kind==Kind::Skill && d.key==skill) { tracked=true; break; } }
	if (!tracked) { return; }
	const auto cap=SkillCap(c,skill);
	if (!cap || c->GetRawSkill(static_cast<EQ::skills::SkillType>(skill))<cap) { return; }
	try {
		if (!Enabled()) { return; }
		const auto s=Read(c);
		auto awards=Awards(c);
		Refresh(c,s,awards);
	} catch (const std::exception &e) { LogError("Earned skill title pending refresh [{}]",e.what()); }
}
void Show(Client *c, unsigned page) {
	try {
		if (!Enabled()) { c->Message(Chat::White,"Earned titles are not enabled."); return; }
		const auto s=Read(c);
		auto awards=Awards(c);
		Refresh(c,s,awards);
		constexpr unsigned size=6;
		const unsigned count=static_cast<unsigned>(sizeof(Catalog)/sizeof(Catalog[0])), pages=(count+size-1)/size;
		if (!page || page>pages) { c->Message(Chat::White,"Usage: #titles [page], 1 through %u.",pages); return; }
		c->Message(Chat::White,"Earned titles - page %u/%u. Select unlocked titles in the Titles window.",page,pages);
		for (unsigned i=(page-1)*size;i<std::min(page*size,count);++i) {
			const auto &d=Catalog[i]; const auto p=Progress(d,s);
			c->Message(Chat::White,"%s [%s; %llu/%llu] - %s",d.name,awards.count(d.id) ? "earned" : "locked",
				static_cast<unsigned long long>(p.first),static_cast<unsigned long long>(p.second),d.description);
		}
	} catch (const std::exception &e) {
		LogError("Earned title progress unavailable [{}]",e.what());
		c->Message(Chat::White,"Title progress is temporarily unavailable. Your saved awards have not been changed.");
	}
}
}
