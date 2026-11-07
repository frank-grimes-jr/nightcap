#pragma once
#include <array>
#include <cstddef>

namespace NightcapLantern {
constexpr unsigned SceneVersion=80, SceneDuration=3600, SceneMembers=6;
enum class Kind { Records, Battle, Defense };
struct Segment {
	Kind kind=Kind::Records;
	unsigned first=0, activities=0, count=0, waves=0;
	bool per_wave=false, escort=false;
};
struct Program { std::array<Segment,3> segments{}; unsigned size=0; };

// Call with actual native activity state, separately for each present member.
// Completed actors cannot recreate quest progress; a lagging helper may replay
// a scene with no additional XP, loot or duplicate equipment entitlement.
template<class Active> int ActiveSegment(const Program &program,Active active) {
	if (!program.size || program.size>program.segments.size()) { return -1; }
	for (unsigned i=0;i<program.size;++i) {
		const auto &segment=program.segments[i];
		for (unsigned n=0;n<segment.activities;++n) {
			if (active(segment.first+n)) { return static_cast<int>(i); }
		}
	}
	return -1;
}
constexpr unsigned WaveCredit(const Segment &segment,unsigned wave) {
	return segment.kind==Kind::Defense && wave && wave<=segment.waves &&
		(segment.per_wave || wave==segment.waves) ? 1 : 0;
}
constexpr bool WaveEligible(const Segment &segment,unsigned wave,unsigned done) {
	return WaveCredit(segment,wave) && (!segment.per_wave || (done<segment.waves && done+1==wave));
}
struct Credit {
	bool connected=false, loaded=false, alive=false, member=false, eligible=false,
		task_active=false, activity_active=false;
	double distance_squared=0;
};
constexpr bool CanCredit(const Credit &credit) {
	return credit.connected && credit.loaded && credit.alive && credit.member && credit.eligible &&
		credit.task_active && credit.activity_active && credit.distance_squared>=0 &&
		credit.distance_squared<=200.0*200.0;
}
}
