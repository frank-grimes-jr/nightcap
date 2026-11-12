#pragma once
#include <algorithm>
#include <cstdint>
#include <map>
#include <set>
#include <string>
#include <utility>
#include <vector>

namespace NightcapTitles {
inline constexpr unsigned TitleBegin = 1900000000, TitleEnd = 1900001000;
enum class Kind { Counter, Skill, AllCrafts, RaidZone, RaidCount, ClearCount, Classic, Planes, Task, Level, BothDragons };
struct Definition {
	unsigned id;
	const char *name;
	bool suffix;
	Kind kind;
	unsigned key, required;
	const char *description;
};
#include "earned_title_catalog.h"
inline constexpr unsigned ClassicZones[] = {36,63,6,44,48,73,32,17,58,11,31,65,66,59,64,18,39,45,72,186,71};
inline constexpr unsigned Crafts[] = {60,61,63,64,65,68,69};
struct Snapshot {
	unsigned level = 0;
	std::map<unsigned, uint64_t> counters;
	std::map<unsigned, std::pair<unsigned, unsigned>> skills; // raw, legal level-50 cap
	std::set<unsigned> clear_zones, raid_zones, tasks;
};
inline unsigned NormalizeZone(unsigned zone) { return zone == 76 ? 186 : zone; }
inline uint64_t Counter(const Snapshot &s, unsigned key) {
	const auto it = s.counters.find(key);
	return it == s.counters.end() ? 0 : it->second;
}
inline bool Mastered(const Snapshot &s, unsigned skill) {
	const auto it = s.skills.find(skill);
	return s.level >= 50 && it != s.skills.end() && it->second.second > 0 && it->second.first >= it->second.second;
}
inline std::pair<uint64_t, uint64_t> Progress(const Definition &d, const Snapshot &s) {
	uint64_t value = 0, required = d.required;
	switch (d.kind) {
	case Kind::Counter: value = Counter(s,d.key); break;
	case Kind::Skill: {
		const auto it=s.skills.find(d.key);
		required=it==s.skills.end() || !it->second.second ? 1 : it->second.second;
		value=it==s.skills.end() || s.level<50 || !it->second.second ? 0 : it->second.first;
		break;
	}
	case Kind::AllCrafts: required=7; for (auto skill : Crafts) { value += Mastered(s,skill); } break;
	case Kind::RaidZone: value=s.raid_zones.count(d.key); break;
	case Kind::RaidCount: value=s.raid_zones.size(); break;
	case Kind::ClearCount: value=s.clear_zones.size(); break;
	case Kind::Classic: required=21; for (auto zone : ClassicZones) { value += s.raid_zones.count(zone); } break;
	case Kind::Planes: required=3; for (auto zone : {72u,186u,71u}) { value += s.raid_zones.count(zone); } break;
	case Kind::Task: value=s.tasks.count(d.key); break;
	case Kind::Level: value=s.level; break;
	case Kind::BothDragons: required=2; value=(Counter(s,100)>0)+(Counter(s,101)>0); break;
	}
	return {std::min(value,required),required};
}
inline bool Earned(const Definition &d, const Snapshot &s) {
	const auto p=Progress(d,s);
	return p.second>0 && p.first>=p.second;
}
inline std::vector<unsigned> KillKeys(unsigned body, unsigned zone, unsigned npc) {
	std::vector<unsigned> keys={1};
	if (body==3 || body==8 || body==12) { keys.push_back(2); }
	if (body==4 || body==9) { keys.push_back(3); }
	if (body==26 || body==29 || body==30 || body==32) { keys.push_back(4); }
	if (zone==32 && npc==32040) { keys.push_back(100); }
	if (zone==73 && npc==73057) { keys.push_back(101); }
	if (zone==72 && npc==72090) { keys.push_back(102); }
	return keys;
}
inline bool CreditEligible(bool player, bool loaded, bool alive, bool nontrivial, bool natural, float distance_squared) {
	return player && loaded && alive && nontrivial && natural && distance_squared<=40000.0f;
}
inline const Definition *Find(unsigned id) {
	for (const auto &d : Catalog) { if (d.id==id) { return &d; } }
	return nullptr;
}
}
