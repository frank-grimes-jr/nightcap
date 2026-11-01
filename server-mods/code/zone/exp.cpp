/*	EQEMu: Everquest Server Emulator
	Copyright (C) 2001-2003 EQEMu Development Team (http://eqemulator.net)

	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; version 2 of the License.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY except by those people which sell it, which
	are required to give you total support for your newly bought product;
	without even the implied warranty of MERCHANTABILITY or FITNESS FOR
	A PARTICULAR PURPOSE. See the GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program; if not, write to the Free Software
	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
*/

#include "common/aa_progression.h"
#include "common/data_bucket.h"
#include "common/data_verification.h"
#include "common/events/player_event_logs.h"
#include "common/features.h"
#include "common/rulesys.h"
#include "common/strings.h"
#include "zone/bot.h"
#include "zone/client.h"
#include "zone/advanced_loot_inventory.h"
#include "zone/dungeon_service.h"
#include "zone/groups.h"
#include "zone/lua_parser.h"
#include "zone/mob.h"
#include "zone/queryserv.h"
#include "zone/quest_parser_collection.h"
#include "zone/raids.h"
#include "zone/string_ids.h"
#include "zone/worldserver.h"

#include <algorithm>
#include <limits>

extern WorldServer worldserver;

extern QueryServ* QServ;

static uint64 ScaleAAXPBasedOnCurrentAATotal(int earnedAA, uint64 add_aaxp)
{
	float baseModifier = RuleR(AA, ModernAAScalingStartPercent);
	int aaMinimum = RuleI(AA, ModernAAScalingAAMinimum);
	int aaLimit = RuleI(AA, ModernAAScalingAALimit);

	// Are we within the scaling window?
	if (earnedAA >= aaLimit || earnedAA < aaMinimum)
	{
		LogDebug("Not within AA scaling window");

		// At or past the limit.  We're done.
		return add_aaxp;
	}

	// We're not at the limit yet.  How close are we?
	int remainingAA = aaLimit - earnedAA;

	// We might not always be X - 0
	int scaleRange = aaLimit - aaMinimum;

	// Normalize and get the effectiveness based on the range and the character's
	// current spent AA.
	float normalizedScale = (float)remainingAA / scaleRange;

	// Scale.
	uint64 totalWithExpMod = add_aaxp * (baseModifier / 100) * normalizedScale;

	// Are we so close to the scale limit that we're earning more XP without scaling?  This
	// will happen when we get very close to the limit.  In this case, just grant the unscaled
	// amount.
	if (totalWithExpMod < add_aaxp)
	{
		return add_aaxp;
	}

	Log(Logs::Detail,
		Logs::None,
		"Total before the modifier %d :: NewTotal %d :: ScaleRange: %d, SpentAA: %d, RemainingAA: %d, normalizedScale: %0.3f",
		add_aaxp, totalWithExpMod, scaleRange, earnedAA, remainingAA, normalizedScale);

	return totalWithExpMod;
}

static uint32 MaxBankedGroupLeadershipPoints(int Level)
{
	if(Level < 35)
		return 4;

	if(Level < 51)
		return 6;

	return 8;
}

static uint32 MaxBankedRaidLeadershipPoints(int Level)
{
	if(Level < 45)
		return 6;

	if(Level < 55)
		return 8;

	return 10;
}

uint64 Client::CalcEXP(uint8 consider_level, bool ignore_modifiers) {
	uint64 in_add_exp = EXP_FORMULA;

	if (XPRate != 0) {
		in_add_exp = static_cast<uint64>(in_add_exp * (static_cast<float>(XPRate) / 100.0f));
	}

	if (!ignore_modifiers) {
		auto total_modifier = 1.0f;
		auto zone_modifier  = 1.0f;

		if (RuleR(Character, ExpMultiplier) >= 0) {
			total_modifier *= RuleR(Character, ExpMultiplier);
		}

		const auto zone_experience = NightcapDungeon::ExperienceModifier(zone->newzone_data.zone_exp_multiplier);
		if (zone_experience >= 0) {
			zone_modifier *= zone_experience;
		}

		if (RuleB(Character, UseRaceClassExpBonuses)) {
			if (
				GetClass() == Class::Warrior ||
				GetClass() == Class::Rogue ||
				GetBaseRace() == Race::Halfling
			) {
				total_modifier *= 1.05;
			}
		}

		if (zone->IsHotzone()) {
			total_modifier += RuleR(Zone, HotZoneBonus);
		}

		in_add_exp = uint64(float(in_add_exp) * total_modifier * zone_modifier);
	}

	if (RuleB(Character,UseXPConScaling)) {
		if (consider_level != 0xFF) {
			switch (consider_level) {
				case ConsiderColor::Gray:
					in_add_exp = 0;
					return 0;
				case ConsiderColor::Green:
					in_add_exp = in_add_exp * RuleI(Character, GreenModifier) / 100;
					break;
				case ConsiderColor::LightBlue:
					in_add_exp = in_add_exp * RuleI(Character, LightBlueModifier) / 100;
					break;
				case ConsiderColor::DarkBlue:
					in_add_exp = in_add_exp * RuleI(Character, BlueModifier) / 100;
					break;
				case ConsiderColor::White:
					in_add_exp = in_add_exp * RuleI(Character, WhiteModifier) / 100;
					break;
				case ConsiderColor::Yellow:
					in_add_exp = in_add_exp * RuleI(Character, YellowModifier) / 100;
					break;
				case ConsiderColor::Red:
					in_add_exp = in_add_exp * RuleI(Character, RedModifier) / 100;
					break;
			}
		}
	}

	if (!ignore_modifiers) {
		if (RuleB(Zone, LevelBasedEXPMods)) {
			if (zone->level_exp_mod[GetLevel()].ExpMod) {
				in_add_exp *= zone->level_exp_mod[GetLevel()].ExpMod;
			}
		}

		if (RuleR(Character, FinalExpMultiplier) >= 0) {
			in_add_exp *= RuleR(Character, FinalExpMultiplier);
		}

		if (RuleB(Character, EnableCharacterEXPMods)) {
			in_add_exp *= zone->GetEXPModifier(this);
		}
	}

	return in_add_exp;
}

uint64 Client::GetExperienceForKill(Mob *against)
{
#ifdef LUA_EQEMU
	uint64 lua_ret = 0;
	bool ignoreDefault = false;
	lua_ret = LuaParser::Instance()->GetExperienceForKill(this, against, ignoreDefault);

	if (ignoreDefault) {
		return lua_ret;
	}
#endif

	if (against && against->IsNPC()) {
		uint32 level = (uint32)against->GetLevel();
		uint64 ret = EXP_FORMULA;

		auto mod = against->GetKillExpMod();
		if(mod >= 0) {
			ret *= mod;
			ret /= 100;
		}

		return ret;
	}

	return 0;
}

float static GetConLevelModifierPercent(uint8 conlevel)
{
	switch (conlevel)
	{
	case ConsiderColor::Green:
		return (float)RuleI(Character, GreenModifier) / 100;
		break;
	case ConsiderColor::LightBlue:
		return (float)RuleI(Character, LightBlueModifier) / 100;
		break;
	case ConsiderColor::DarkBlue:
		return (float)RuleI(Character, BlueModifier) / 100;
		break;
	case ConsiderColor::White:
		return (float)RuleI(Character, WhiteModifier) / 100;
		break;
	case ConsiderColor::Yellow:
		return (float)RuleI(Character, YellowModifier) / 100;
		break;
	case ConsiderColor::Red:
		return (float)RuleI(Character, RedModifier) / 100;
		break;
	default:
		return 0;
	}
}

void Client::CalculateNormalizedAAExp(uint64 &add_aaxp, uint8 conlevel, bool resexp)
{
	// Functionally this is the same as having the case in the switch, but this is
	// cleaner to read.
	if (ConsiderColor::Gray == conlevel || resexp)
	{
		add_aaxp = 0;
		return;
	}

	// For this, we ignore the provided value of add_aaxp because it doesn't
	// apply.  XP per AA is normalized such that there are X white con kills
	// per AA.

	uint32 whiteConKillsPerAA = RuleI(AA, NormalizedAANumberOfWhiteConPerAA);
	uint32 xpPerAA = RuleI(AA, ExpPerPoint);

	float colorModifier = GetConLevelModifierPercent(conlevel);
	// Calculate the full award; passive scaling happens after AA modifiers/caps.
	add_aaxp = whiteConKillsPerAA > 0 && colorModifier > 0
		? xpPerAA / (whiteConKillsPerAA / colorModifier) : 0;
}

void Client::CalculateStandardAAExp(uint64 &add_aaxp, uint8 conlevel, bool resexp)
{
	if (!resexp)
	{
		//if XP scaling is based on the con of a monster, do that now.
		if (RuleB(Character, UseXPConScaling))
		{
			if (conlevel != 0xFF && !resexp)
			{
				add_aaxp *= GetConLevelModifierPercent(conlevel);
			}
		}
	}	//end !resexp

	float aatotalmod = 1.0;
	const auto zone_experience = NightcapDungeon::ExperienceModifier(zone->newzone_data.zone_exp_multiplier);
	if (zone_experience >= 0) {
		aatotalmod *= zone_experience;
	}

	// Shouldn't race not affect AA XP?
	if (RuleB(Character, UseRaceClassExpBonuses))
	{
		if (GetBaseRace() == Race::Halfling) {
			aatotalmod *= 1.05;
		}

		if (GetClass() == Class::Rogue || GetClass() == Class::Warrior) {
			aatotalmod *= 1.05;
		}
	}

	// why wasn't this here? Where should it be?
	if (zone->IsHotzone())
	{
		aatotalmod += RuleR(Zone, HotZoneBonus);
	}

	if (RuleB(Zone, LevelBasedEXPMods)) {
		if (zone->level_exp_mod[GetLevel()].ExpMod) {
			add_aaxp *= zone->level_exp_mod[GetLevel()].AAExpMod;
		}
	}

	if (RuleR(Character, FinalExpMultiplier) >= 0) {
		add_aaxp *= RuleR(Character, FinalExpMultiplier);
	}

	if (RuleB(Character, EnableCharacterEXPMods)) {
		add_aaxp *= zone->GetAAEXPModifier(this);
	}

	add_aaxp = (uint64)(RuleR(Character, AAExpMultiplier) * add_aaxp * aatotalmod);
}

void Client::CalculateLeadershipExp(uint64 &add_exp, uint8 conlevel)
{
	if (IsLeadershipEXPOn() && (conlevel == ConsiderColor::DarkBlue || conlevel == ConsiderColor::White || conlevel == ConsiderColor::Yellow || conlevel == ConsiderColor::Red))
	{
		add_exp = static_cast<uint64>(static_cast<float>(add_exp) * 0.8f);

		if (GetGroup())
		{
			if (m_pp.group_leadership_points < MaxBankedGroupLeadershipPoints(GetLevel())
				&& RuleI(Character, KillsPerGroupLeadershipAA) > 0)
			{
				uint64 exp = GROUP_EXP_PER_POINT / RuleI(Character, KillsPerGroupLeadershipAA);
				Client *mentoree = GetGroup()->GetMentoree();
				if (GetGroup()->GetMentorPercent() && mentoree &&
					mentoree->GetGroupPoints() < MaxBankedGroupLeadershipPoints(mentoree->GetLevel()))
				{
					uint64 mentor_exp = exp * (GetGroup()->GetMentorPercent() / 100.0f);
					exp -= mentor_exp;
					mentoree->AddLeadershipEXP(mentor_exp, 0); // ends up rounded down
					mentoree->MessageString(Chat::LeaderShip, GAIN_GROUP_LEADERSHIP_EXP);
				}
				if (exp > 0)
				{
					// possible if you mentor 100% to the other client
					AddLeadershipEXP(exp, 0); // ends up rounded up if mentored, no idea how live actually does it
					MessageString(Chat::LeaderShip, GAIN_GROUP_LEADERSHIP_EXP);
				}
			}
			else
			{
				MessageString(Chat::LeaderShip, MAX_GROUP_LEADERSHIP_POINTS);
			}
		}
		else
		{
			Raid *raid = GetRaid();
			// Raid leaders CAN NOT gain group AA XP, other group leaders can though!
			if (raid->IsLeader(this))
			{
				if (m_pp.raid_leadership_points < MaxBankedRaidLeadershipPoints(GetLevel())
					&& RuleI(Character, KillsPerRaidLeadershipAA) > 0)
				{
					AddLeadershipEXP(0, RAID_EXP_PER_POINT / RuleI(Character, KillsPerRaidLeadershipAA));
					MessageString(Chat::LeaderShip, GAIN_RAID_LEADERSHIP_EXP);
				}
				else
				{
					MessageString(Chat::LeaderShip, MAX_RAID_LEADERSHIP_POINTS);
				}
			}
			else
			{
				if (m_pp.group_leadership_points < MaxBankedGroupLeadershipPoints(GetLevel())
					&& RuleI(Character, KillsPerGroupLeadershipAA) > 0)
				{
					uint32 group_id = raid->GetGroup(this);
					uint64 exp = GROUP_EXP_PER_POINT / RuleI(Character, KillsPerGroupLeadershipAA);
					Client *mentoree = raid->GetMentoree(group_id);
					if (raid->GetMentorPercent(group_id) && mentoree &&
						mentoree->GetGroupPoints() < MaxBankedGroupLeadershipPoints(mentoree->GetLevel()))
					{
						uint64 mentor_exp = exp * (raid->GetMentorPercent(group_id) / 100.0f);
						exp -= mentor_exp;
						mentoree->AddLeadershipEXP(mentor_exp, 0);
						mentoree->MessageString(Chat::LeaderShip, GAIN_GROUP_LEADERSHIP_EXP);
					}
					if (exp > 0)
					{
						AddLeadershipEXP(exp, 0);
						MessageString(Chat::LeaderShip, GAIN_GROUP_LEADERSHIP_EXP);
					}
				}
				else
				{
					MessageString(Chat::LeaderShip, MAX_GROUP_LEADERSHIP_POINTS);
				}
			}
		}
	}
}

void Client::CalculateExp(uint64 in_add_exp, uint64 &add_exp, uint64 &add_aaxp, uint8 conlevel, bool resexp, uint64 *full_exp)
{
	add_exp = in_add_exp;

	if (!resexp && (XPRate != 0))
	{
		add_exp = static_cast<uint64>(in_add_exp * (static_cast<float>(XPRate) / 100.0f));
	}

	// Make sure it was initialized.
	add_aaxp = 0;

	if (!resexp)
	{
		// Retain the full raw AA basis for legacy mode; split normal XP after modifiers.
		add_aaxp = add_exp;

		float totalmod = 1.0;
		float zemmod = 1.0;

		//get modifiers
		if (RuleR(Character, ExpMultiplier) >= 0) {
			totalmod *= RuleR(Character, ExpMultiplier);
		}

		//add the zone exp modifier.
		const auto zone_experience = NightcapDungeon::ExperienceModifier(zone->newzone_data.zone_exp_multiplier);
		if (zone_experience >= 0) {
			zemmod *= zone_experience;
		}

		if (RuleB(Character, UseRaceClassExpBonuses))
		{
			if (GetBaseRace() == Race::Halfling) {
				totalmod *= 1.05;
			}

			if (GetClass() == Class::Rogue || GetClass() == Class::Warrior) {
				totalmod *= 1.05;
			}
		}

		//add hotzone modifier if one has been set.
		if (zone->IsHotzone())
		{
			totalmod += RuleR(Zone, HotZoneBonus);
		}

		add_exp = uint64(float(add_exp) * totalmod * zemmod);

		//if XP scaling is based on the con of a monster, do that now.
		if (RuleB(Character, UseXPConScaling))
		{
			if (conlevel != 0xFF && !resexp)
			{
				add_exp = add_exp * GetConLevelModifierPercent(conlevel);
			}
		}

		// Calculate any changes to leadership experience.
		CalculateLeadershipExp(add_exp, conlevel);
	}	//end !resexp

	if (RuleB(Zone, LevelBasedEXPMods)) {
		if (zone->level_exp_mod[GetLevel()].ExpMod) {
			add_exp *= zone->level_exp_mod[GetLevel()].ExpMod;
		}
	}

	if (RuleR(Character, FinalExpMultiplier) >= 0) {
		add_exp *= RuleR(Character, FinalExpMultiplier);
	}

	if (RuleB(Character, EnableCharacterEXPMods)) {
		add_exp *= zone->GetEXPModifier(this);
	}

	//Enforce Percent XP Cap per kill, if rule is enabled
	int kill_percent_xp_cap = RuleI(Character, ExperiencePercentCapPerKill);
	if (kill_percent_xp_cap >= 0) {
		auto experience_for_level = (GetEXPForLevel(GetLevel() + 1) - GetEXPForLevel(GetLevel()));
		float exp_percent = (float)((float)add_exp / (float)(GetEXPForLevel(GetLevel() + 1) - GetEXPForLevel(GetLevel()))) * (float)100; //EXP needed for level
		if (exp_percent > kill_percent_xp_cap) {
			add_exp = static_cast<uint64>(std::floor(experience_for_level * (kill_percent_xp_cap / 100.0f)));
		}
	}

	if (full_exp) { *full_exp = resexp ? 0 : add_exp; }
	if (!resexp) {
		if (RuleI(AA, LevelBasedPointsPerLevel) > 0) {
			// Same modified XP basis at every allocation, before level-cap clamping.
			add_aaxp = add_exp;
		}
		add_exp = AAProgression::LevelShare(add_exp, m_epp.perAA);
	}
	add_exp = GetEXP() + add_exp;
}

uint64 Client::CalculateLevelBasedAAExp(uint64 full_xp, uint64 level_xp)
{
	int max_level = RuleI(Character, MaxExpLevel);
	if (max_level <= 0) {
		max_level = RuleI(Character, MaxLevel);
	}
	if (GetClientMaxLevel()) {
		max_level = GetClientMaxLevel();
	}
	return AAProgression::Award(full_xp, level_xp, GetEXP(), GetLevel(),
		std::clamp(max_level, 1, 126), m_epp.perAA,
		PassiveAAPercent(),
		std::clamp(RuleI(AA, LevelBasedPointsPerLevel), 0, 1000),
		GetRequiredAAExperience(), [this](uint16 level) { return GetEXPForLevel(level); });
}

// SSF characters earn AA only from the allocation they choose in the AA window.
uint32 Client::PassiveAAPercent() const
{
	return IsSSF() ? 0 : std::clamp(RuleI(AA, PassiveExpPercent), 0, 100);
}

void Client::NormalizeAAAllocation()
{
	// A full AA bank must never silently resume leveling at 100% allocation.
	if (GetLevel() < RuleI(Character, AAExpMinLevel) || m_epp.perAA > 100) {
		m_epp.perAA = 0;
	}
}

// Input is a full, modified AA award. Return the new total for SetEXP, which
// owns point conversion, events and client updates. Never erase existing AAs.
uint64 Client::FinalizeAAExperience(uint64 aaexp, bool level_scaled)
{
	const uint64 current = GetAAXP();
	const int cap = RuleI(AA, UnusedAAPointCap);
	if (GetLevel() < RuleI(Character, AAExpMinLevel)
		|| (cap >= 0 && GetAAPoints() >= static_cast<uint32>(cap))) {
		return current;
	}

	// Are we also doing linear AA acceleration?
	if (!level_scaled && RuleB(AA, ModernAAScalingEnabled) && aaexp > 0)
	{
		aaexp = ScaleAAXPBasedOnCurrentAATotal(GetSpentAA() + GetAAPoints(), aaexp);
	}

	// Check for AA XP Cap
	if (RuleI(AA, MaxAAEXPPerKill) >= 0 && aaexp > static_cast<uint64>(RuleI(AA, MaxAAEXPPerKill))) {
		aaexp = RuleI(AA, MaxAAEXPPerKill);
	}

	if (!level_scaled) {
		const uint64 passive = PassiveAAPercent();
		const uint64 weight = m_epp.perAA * 100 + passive * (100 - m_epp.perAA);
		// Passive AA follows the retained leveling fraction; never double-pay focus.
		aaexp = (aaexp / 10000) * weight + (aaexp % 10000) * weight / 10000;
	}

	// Bound the total before addition and before SetEXP converts it to points.
	uint64 limit = std::numeric_limits<uint32>::max();
	if (cap >= 0) {
		limit = std::min(limit, (static_cast<uint64>(cap) - GetAAPoints()) * GetRequiredAAExperience());
	}
	return current + std::min(aaexp, limit > current ? limit - current : uint64(0));
}

void Client::AddEXP(ExpSource exp_source, uint64 in_add_exp, uint8 conlevel, bool resexp, NPC* npc) {
	if (!IsEXPEnabled()) {
		return;
	}

	NormalizeAAAllocation();
	uint64 exp = 0;
	uint64 aaexp = 0;
	uint64 item_exp = 0;
	CalculateExp(in_add_exp, exp, aaexp, conlevel, resexp, &item_exp);
	if (RuleB(Items, PowerSourceItemXP) && exp_source == ExpSource::Kill && !resexp && npc &&
		conlevel != ConsiderColor::Gray && conlevel != 0xFF && !npc->HasOwner() && !npc->IsMerc() &&
		!npc->GetSwarmInfo() && !npc->GetSwarmOwner()) {
		if (NightcapLoot::AwardItemExperience(this, item_exp) == NightcapLoot::TransferResult::Uncertain) { return; }
	}
	const bool level_scaled = RuleI(AA, LevelBasedPointsPerLevel) > 0;
	const bool progression = exp_source == ExpSource::Kill || exp_source == ExpSource::Quest || exp_source == ExpSource::Task;
	if (!resexp && aaexp > 0 && (progression || (!level_scaled && m_epp.perAA > 0))) {
		if (level_scaled) {
			aaexp = exp_source == ExpSource::Kill && conlevel == ConsiderColor::Gray ? 0
				: CalculateLevelBasedAAExp(aaexp, exp - GetEXP());
		} else if (RuleB(AA, NormalizedAAEnabled) && exp_source == ExpSource::Kill && conlevel != 0xFF) {
			CalculateNormalizedAAExp(aaexp, conlevel, false);
		} else {
			CalculateStandardAAExp(aaexp, conlevel, false);
		}
	} else {
		aaexp = 0;
	}
	aaexp = FinalizeAAExperience(aaexp, level_scaled);

	// Now update our character's normal and AA xp
	SetEXP(exp_source, exp, aaexp, resexp, npc);
}

void Client::SetEXP(ExpSource exp_source, uint64 set_exp, uint64 set_aaxp, bool isrezzexp, NPC* npc) {
	uint64 current_exp = GetEXP();
	uint64 current_aa_exp = GetAAXP();
	uint64 total_current_exp = current_exp + current_aa_exp;
	uint64 total_add_exp = set_exp + set_aaxp;

#ifdef LUA_EQEMU
	uint64 lua_ret = 0;
	bool ignore_default = false;
	lua_ret = LuaParser::Instance()->SetEXP(this, exp_source, current_exp, set_exp, isrezzexp, ignore_default);
	if (ignore_default) {
		set_exp = lua_ret;
	}

	lua_ret = 0;
	ignore_default = false;
	lua_ret = LuaParser::Instance()->SetAAEXP(this, exp_source, current_aa_exp, set_aaxp, isrezzexp, ignore_default);
	if (ignore_default) {
		set_aaxp = lua_ret;
	}
	total_add_exp = set_exp + set_aaxp;
#endif

	LogDebug("Attempting to Set Exp for [{}] (XP: [{}], AAXP: [{}], Rez: [{}])", GetCleanName(), set_exp, set_aaxp, isrezzexp ? "true" : "false");

	auto max_AAXP = GetRequiredAAExperience();
	if (max_AAXP == 0 || GetEXPForLevel(GetLevel()) == 0xFFFFFFFF) {
		Message(Chat::Red, "Error in Client::SetEXP. EXP not set.");
		return; // Must be invalid class/race
	}

	uint32 i = 0;
	uint32 membercount = 0;
	if(GetGroup()) {
		for (i = 0; i < MAX_GROUP_MEMBERS; i++) {
			if (GetGroup()->members[i] != nullptr) {
				membercount++;
			}
		}
	}

	if (total_add_exp > total_current_exp) {
		uint64 exp_gained = set_exp - current_exp;
		uint64 aa_exp_gained = set_aaxp - current_aa_exp;
		float exp_percent = (float)((float)exp_gained / (float)(GetEXPForLevel(GetLevel() + 1) - GetEXPForLevel(GetLevel())))*(float)100; //EXP needed for level
		float aa_exp_percent = (float)((float)aa_exp_gained / (float)(RuleI(AA, ExpPerPoint)))*(float)100; //AAEXP needed for level
		std::string exp_amount_message = "";
		if (RuleI(Character, ShowExpValues) >= 1) {
			if (exp_gained > 0 && aa_exp_gained > 0) {
				exp_amount_message = fmt::format("({}) ({})", exp_gained, aa_exp_gained);
			} else if (exp_gained > 0) {
				exp_amount_message = fmt::format("({})", exp_gained);
			} else {
				exp_amount_message = fmt::format("({}) AA", aa_exp_gained);
			}
		}

		std::string exp_percent_message = "";
		if (RuleI(Character, ShowExpValues) >= 2) {
			if (exp_gained > 0 && aa_exp_gained > 0) {
				exp_percent_message = StringFormat("(%.3f%%, %.3f%%AA)", exp_percent, aa_exp_percent);
			} else if (exp_gained > 0) {
				exp_percent_message = StringFormat("(%.3f%%)", exp_percent);
			} else {
				exp_percent_message = StringFormat("(%.3f%%AA)", aa_exp_percent);
			}
		}
		if (isrezzexp) {
			if (RuleI(Character, ShowExpValues) > 0) {
				Message(Chat::Experience, "You regain %s experience from resurrection. %s", exp_amount_message.c_str(), exp_percent_message.c_str());
			} else {
				MessageString(Chat::Experience, REZ_REGAIN);
			}
		} else {
			if (membercount > 1) {
				if (RuleI(Character, ShowExpValues) > 0) {
					Message(Chat::Experience, "You have gained %s party experience! %s", exp_amount_message.c_str(), exp_percent_message.c_str());
				} else if (zone->IsHotzone()) {
					Message(Chat::Experience, "You gain party experience (with a bonus)!");
				} else {
					MessageString(Chat::Experience, GAIN_GROUPXP);
				}
			} else if (IsRaidGrouped()) {
				if (RuleI(Character, ShowExpValues) > 0) {
					Message(Chat::Experience, "You have gained %s raid experience! %s", exp_amount_message.c_str(), exp_percent_message.c_str());
				} else if (zone->IsHotzone()) {
					Message(Chat::Experience, "You gained raid experience (with a bonus)!");
				} else {
					MessageString(Chat::Experience, GAIN_RAIDEXP);
				}
			} else {
				if (RuleI(Character, ShowExpValues) > 0) {
					Message(Chat::Experience, "You have gained %s experience! %s", exp_amount_message.c_str(), exp_percent_message.c_str());
				} else if (zone->IsHotzone()) {
					Message(Chat::Experience, "You gain experience (with a bonus)!");
				} else {
					MessageString(Chat::Experience, GAIN_XP);
				}
			}
		}
		ProcessEvolvingItem(exp_gained, npc);
	} else if(total_add_exp < total_current_exp) { //only loss message if you lose exp, no message if you gained/lost nothing.
		uint64 exp_lost = current_exp - set_exp;
		float exp_percent = (float)((float)exp_lost / (float)(GetEXPForLevel(GetLevel() + 1) - GetEXPForLevel(GetLevel())))*(float)100;

		if (RuleI(Character, ShowExpValues) == 1 && exp_lost > 0) {
			Message(Chat::Yellow, "You have lost %i experience.", exp_lost);
		} else if (RuleI(Character, ShowExpValues) == 2 && exp_lost > 0) {
			Message(Chat::Yellow, "You have lost %i experience. (%.3f%%)", exp_lost, exp_percent);
		} else {
			Message(Chat::Yellow, "You have lost experience.");
		}
	}

	//check_level represents the level we should be when we have
	//this ammount of exp (once these loops complete)
	uint16 check_level = GetLevel()+1;
	//see if we gained any levels
	bool level_increase = true;
	int8 level_count = 0;

	while (set_exp >= GetEXPForLevel(check_level)) {
		check_level++;
		if (check_level > 127) {	//hard level cap
			check_level = 127;
			break;
		}
		level_count++;

		if (GetMercenaryID()) {
			UpdateMercLevel();
		}
	}
	//see if we lost any levels
	while (set_exp < GetEXPForLevel(check_level-1)) {
		check_level--;
		if (check_level < 2) {	//hard level minimum
			check_level = 2;
			break;
		}
		level_increase = false;
		if (GetMercenaryID()) {
			UpdateMercLevel();
		}
	}
	check_level--;


	//see if we gained any AAs
	if (set_aaxp >= max_AAXP) {
		/*
			Note: AA exp is stored differently than normal exp.
			Exp points are only stored in m_pp.expAA until you
			gain a full AA point, once you gain it, a point is
			added to m_pp.aapoints and the ammount needed to gain
			that point is subtracted from m_pp.expAA

			then, once they spend an AA point, it is subtracted from
			m_pp.aapoints. In theory it then goes into m_pp.aapoints_spent,
			but im not sure if we have that in the right spot.
		*/
		//record how many points we have
		uint32 last_unspentAA = m_pp.aapoints;

		//figure out how many AA points we get from the exp were setting
		m_pp.aapoints = set_aaxp / max_AAXP;
		LogDebug("Calculating additional AA Points from AAXP for [{}]: [{}] / [{}] = [{}] points", GetCleanName(), set_aaxp, max_AAXP, (float)set_aaxp / (float)max_AAXP);

		//get remainder exp points, set in PP below
		set_aaxp = set_aaxp - (max_AAXP * m_pp.aapoints);

		//add in how many points we had
		m_pp.aapoints += last_unspentAA;

		//figure out how many points were actually gained
		uint32 gained = (m_pp.aapoints - last_unspentAA);

		//Message(Chat::Yellow, "You have gained %d skill points!!", m_pp.aapoints - last_unspentAA);
		char val1[20] = { 0 };
		char val2[20] = { 0 };

		if (gained == 1 && m_pp.aapoints == 1) {
			MessageString(Chat::Experience, GAIN_SINGLE_AA_SINGLE_AA, ConvertArray(m_pp.aapoints, val1)); //You have gained an ability point!  You now have %1 ability point.
		} else if (gained == 1 && m_pp.aapoints > 1) {
			MessageString(Chat::Experience, GAIN_SINGLE_AA_MULTI_AA, ConvertArray(m_pp.aapoints, val1)); //You have gained an ability point!  You now have %1 ability points.
		} else {
			MessageString(Chat::Experience, GAIN_MULTI_AA_MULTI_AA, ConvertArray(gained, val1), ConvertArray(m_pp.aapoints, val2)); //You have gained %1 ability point(s)!  You now have %2 ability point(s).
		}

		if (RuleB(AA, SoundForAAEarned)) {
			SendSound();
		}

		if (parse->PlayerHasQuestSub(EVENT_AA_GAIN)) {
			parse->EventPlayer(EVENT_AA_GAIN, this, std::to_string(gained), 0);
		}

		RecordPlayerEventLog(PlayerEvent::AA_GAIN, PlayerEvent::AAGainedEvent{gained});

		/* QS: PlayerLogAARate */
		if (RuleB(QueryServ, PlayerLogAARate)) {
			int add_points = (m_pp.aapoints - last_unspentAA);
			std::string query = StringFormat("INSERT INTO `qs_player_aa_rate_hourly` (char_id, aa_count, hour_time) VALUES (%i, %i, UNIX_TIMESTAMP() - MOD(UNIX_TIMESTAMP(), 3600)) ON DUPLICATE KEY UPDATE `aa_count` = `aa_count` + %i", CharacterID(), add_points, add_points);
			QServ->SendQuery(query.c_str());
		}

		//Message(Chat::Yellow, "You now have %d skill points available to spend.", m_pp.aapoints);
	}

	uint8 max_level = RuleI(Character, MaxExpLevel) + 1;

	if (max_level <= 1) {
		max_level = RuleI(Character, MaxLevel) + 1;
	}

	auto client_max_level = GetClientMaxLevel();
	if (client_max_level) {
		max_level = client_max_level + 1;
	}

	if (check_level > max_level) {
		check_level = max_level;

		if (RuleB(Character, KeepLevelOverMax)) {
			set_exp = GetEXPForLevel(GetLevel()+1);
		} else {
			set_exp = GetEXPForLevel(max_level);
		}
	}

	if ((GetLevel() != check_level) && !(check_level >= max_level)) {
		char val1[20]={0};
		if (level_increase) {
			if (level_count == 1) {
				MessageString(Chat::Experience, GAIN_LEVEL, ConvertArray(check_level, val1));
			} else {
				Message(Chat::Yellow, "Welcome to level %i!", check_level);
			}

			if (check_level == RuleI(Character, DeathItemLossLevel) &&
			    m_ClientVersionBit & EQ::versions::maskUFAndEarlier) {
				MessageString(Chat::Yellow, CORPSE_ITEM_LOST);
				}

			if (check_level == RuleI(Character, DeathExpLossLevel)) {
				MessageString(Chat::Yellow, CORPSE_EXP_LOST);
			}
		}

		uint8 myoldlevel = GetLevel();

		SetLevel(check_level);

		if (RuleB(Bots, Enabled) && RuleB(Bots, BotLevelsWithOwner)) {
			// hack way of doing this..but, least invasive... (same criteria as gain level for sendlvlapp)
			Bot::LevelBotWithClient(this, GetLevel(), (myoldlevel == check_level - 1));
		}
	}

	//If were at max level then stop gaining experience if we make it to the cap
	if (GetLevel() == max_level - 1){
		uint32 expneeded = GetEXPForLevel(max_level);
		if (set_exp > expneeded) {
			set_exp = expneeded;
		}
	}

	if (parse->PlayerHasQuestSub(EVENT_EXP_GAIN) && m_pp.exp != set_exp) {
		parse->EventPlayer(EVENT_EXP_GAIN, this, std::to_string(set_exp - m_pp.exp), 0);
	}

	if (parse->PlayerHasQuestSub(EVENT_AA_EXP_GAIN) && m_pp.expAA != set_aaxp) {
		parse->EventPlayer(EVENT_AA_EXP_GAIN, this, std::to_string(set_aaxp - m_pp.expAA), 0);
	}

	//set the client's EXP and AAEXP
	m_pp.exp = set_exp;
	m_pp.expAA = set_aaxp;

	if (GetLevel() < RuleI(Character, AAExpMinLevel)) {
		m_epp.perAA = 0;	// turn off aa exp below the AA min level
	} else {
		SendAlternateAdvancementStats();    //otherwise, send them an AA update
	}

	//send the expdata in any case so the xp bar isnt stuck after leveling
	uint32 tmpxp1 = GetEXPForLevel(GetLevel()+1);
	uint32 tmpxp2 = GetEXPForLevel(GetLevel());
	// Quag: crash bug fix... Divide by zero when tmpxp1 and 2 equalled each other, most likely the error case from GetEXPForLevel() (invalid class, etc)
	if (tmpxp1 != tmpxp2 && tmpxp1 != 0xFFFFFFFF && tmpxp2 != 0xFFFFFFFF) {
		auto outapp = new EQApplicationPacket(OP_ExpUpdate, sizeof(ExpUpdate_Struct));
		ExpUpdate_Struct* eu = (ExpUpdate_Struct*)outapp->pBuffer;
		float tmpxp = (float) ( (float) set_exp-tmpxp2 ) / ( (float) tmpxp1-tmpxp2 );
		eu->exp = (uint32)(330.0f * tmpxp);
		FastQueuePacket(&outapp);
	}

	if (admin >= AccountStatus::GMAdmin && GetGM()) {
		char val1[20]={0};
		char val2[20]={0};
		char val3[20]={0};
		MessageString(Chat::Experience, GM_GAINXP, ConvertArray(set_aaxp,val1),ConvertArray(set_exp,val2),ConvertArray(GetEXPForLevel(GetLevel()+1),val3));	//[GM] You have gained %1 AXP and %2 EXP (%3).
	}
}

void Client::SetLevel(uint8 set_level, bool command)
{
	if (GetEXPForLevel(set_level) == 0xFFFFFFFF) {
		LogError("GetEXPForLevel([{}]) = 0xFFFFFFFF", set_level);
		return;
	}

	auto outapp = new EQApplicationPacket(OP_LevelUpdate, sizeof(LevelUpdate_Struct));
	auto* lu = (LevelUpdate_Struct *) outapp->pBuffer;
	lu->level = set_level;

	if (m_pp.level2 != 0) {
		lu->level_old = m_pp.level2;
	} else {
		lu->level_old = level;
	}

	level = set_level;

	if (IsRaidGrouped()) {
		Raid *r = GetRaid();
		if (r) {
			r->UpdateLevel(GetName(), set_level);
		}
	}

	if (set_level > m_pp.level2) {
		if (m_pp.level2 == 0) {
			m_pp.points += 5;
		} else {
			m_pp.points += (5 * (set_level - m_pp.level2));
		}

		m_pp.level2 = set_level;
	}

	if (set_level > m_pp.level) {
		int levels_gained = (set_level - m_pp.level);

		ReconcileMulticlassSkills();

		if (parse->PlayerHasQuestSub(EVENT_LEVEL_UP)) {
			parse->EventPlayer(EVENT_LEVEL_UP, this, std::to_string(levels_gained), 0);
		}

		if (PlayerEventLogs::Instance()->IsEventEnabled(PlayerEvent::LEVEL_GAIN)) {
			auto e = PlayerEvent::LevelGainedEvent{
				.from_level = m_pp.level,
				.to_level = set_level,
				.levels_gained = levels_gained
			};

			RecordPlayerEventLog(PlayerEvent::LEVEL_GAIN, e);
		}
	} else if (set_level < m_pp.level) {
		int levels_lost = (m_pp.level - set_level);

		if (parse->PlayerHasQuestSub(EVENT_LEVEL_DOWN)) {
			parse->EventPlayer(EVENT_LEVEL_DOWN, this, std::to_string(levels_lost), 0);
		}

		if (PlayerEventLogs::Instance()->IsEventEnabled(PlayerEvent::LEVEL_LOSS)) {
			auto e = PlayerEvent::LevelLostEvent{
				.from_level = m_pp.level,
				.to_level = set_level,
				.levels_lost = levels_lost
			};

			RecordPlayerEventLog(PlayerEvent::LEVEL_LOSS, e);
		}
	}

	m_pp.level = set_level;
	// Re-evaluate usable ranks before bonuses or a profile save, retaining paid ranks.
	if (ReprojectEarnedAAs()) {
		SendClearPlayerAA();
		SendLoadedAlternateAdvancementTable();
		SendAlternateAdvancementPoints();
	}

	if (command) {
		m_pp.exp = GetEXPForLevel(set_level);
		Message(Chat::Yellow, fmt::format("Welcome to level {}!", set_level).c_str());
		lu->exp = 0;

		AutoGrantAAPoints();
	} else {
		const auto temporary_xp = (
			static_cast<float>(m_pp.exp - GetEXPForLevel(GetLevel())) /
			static_cast<float>(GetEXPForLevel(GetLevel() + 1) - GetEXPForLevel(GetLevel()))
		);
		lu->exp = static_cast<uint32>(330.0f * temporary_xp);
	}

	QueuePacket(outapp);
	safe_delete(outapp);
	SendAppearancePacket(AppearanceType::WhoLevel, set_level); // who level change

	LogInfo("Setting Level for [{}] to [{}]", GetName(), set_level);

	CalcBonuses();

	if (!RuleB(Character, HealOnLevel)) {
		const auto max_hp = CalcMaxHP();
		if (GetHP() > max_hp) {
			SetHP(max_hp);
		}
	} else {
		SetHP(CalcMaxHP()); // Why not, lets give them a free heal
	}

	if (RuleI(World, PVPMinLevel) > 0 && level >= RuleI(World, PVPMinLevel) && m_pp.pvp == 0) {
		SetPVP(true);
	}

	if (IsInAGuild()) {
		guild_mgr.SendToWorldMemberLevelUpdate(GuildID(), GetLevel(), std::string(GetCleanName()));
		DoGuildTributeUpdate();
	}

	DoTributeUpdate();
	SendHPUpdate();
	SetMana(CalcMaxMana());
	UpdateWho();

	UpdateMercLevel();

	Save();
}

// Note: The client calculates exp separately, we cant change this function
// Add: You can set the values you want now, client will be always sync :) - Merkur
uint32 Client::GetEXPForLevel(uint16 check_level)
{
#ifdef LUA_EQEMU
	uint32 lua_ret = 0;
	bool ignoreDefault = false;
	lua_ret = LuaParser::Instance()->GetEXPForLevel(this, check_level, ignoreDefault);

	if (ignoreDefault) {
		return lua_ret;
	}
#endif

	uint16 check_levelm1 = check_level-1;
	float mod;
	if (check_level < 31)
		mod = 1.0;
	else if (check_level < 36)
		mod = 1.1;
	else if (check_level < 41)
		mod = 1.2;
	else if (check_level < 46)
		mod = 1.3;
	else if (check_level < 52)
		mod = 1.4;
	else if (check_level < 53)
		mod = 1.5;
	else if (check_level < 54)
		mod = 1.6;
	else if (check_level < 55)
		mod = 1.7;
	else if (check_level < 56)
		mod = 1.9;
	else if (check_level < 57)
		mod = 2.1;
	else if (check_level < 58)
		mod = 2.3;
	else if (check_level < 59)
		mod = 2.5;
	else if (check_level < 60)
		mod = 2.7;
	else if (check_level < 61)
		mod = 3.0;
	else
		mod = 3.1;

	float base = (check_levelm1)*(check_levelm1)*(check_levelm1);

	mod *= 1000;

	uint32 finalxp = uint32(base * mod);

	if(RuleB(Character,UseOldRaceExpPenalties))
	{
		float racemod = 1.0;
		if(GetBaseRace() == Race::Troll || GetBaseRace() == Race::Iksar) {
			racemod = 1.2;
		} else if(GetBaseRace() == Race::Ogre) {
			racemod = 1.15;
		} else if(GetBaseRace() == Race::Barbarian) {
			racemod = 1.05;
		} else if(GetBaseRace() == Race::Halfling) {
			racemod = 0.95;
		}

		finalxp = uint64(finalxp * racemod);
	}

	if(RuleB(Character,UseOldClassExpPenalties))
	{
		float classmod = 1.0;
		if(GetClass() == Class::Paladin || GetClass() == Class::ShadowKnight || GetClass() == Class::Ranger || GetClass() == Class::Bard) {
			classmod = 1.4;
		} else if(GetClass() == Class::Monk) {
			classmod = 1.2;
		} else if(GetClass() == Class::Wizard || GetClass() == Class::Enchanter || GetClass() == Class::Magician || GetClass() == Class::Necromancer) {
			classmod = 1.1;
		} else if(GetClass() == Class::Rogue) {
			classmod = 0.91;
		} else if(GetClass() == Class::Warrior) {
			classmod = 0.9;
		}

		finalxp = uint64(finalxp * classmod);
	}

	return finalxp;
}

void Client::AddLevelBasedExp(ExpSource exp_source, uint8 exp_percentage, uint8 max_level, bool ignore_mods)
{
	if (!IsEXPEnabled()) {
		return;
	}
	NormalizeAAAllocation();
	uint64	award;
	uint64	xp_for_level;

	if (exp_percentage > 100)
	{
		exp_percentage = 100;
	}

	if (!max_level || GetLevel() < max_level)
	{
		max_level = GetLevel();
	}

	xp_for_level = GetEXPForLevel(max_level + 1) - GetEXPForLevel(max_level);
	award = xp_for_level * exp_percentage / 100;
	uint64 aaexp = award;

	if (RuleB(Zone, LevelBasedEXPMods) && !ignore_mods) {
		if (zone->level_exp_mod[GetLevel()].ExpMod) {
			award *= zone->level_exp_mod[GetLevel()].ExpMod;
			aaexp *= zone->level_exp_mod[GetLevel()].AAExpMod;
		}
	}

	if (RuleR(Character, FinalExpMultiplier) >= 0) {
		award *= RuleR(Character, FinalExpMultiplier);
		aaexp *= RuleR(Character, FinalExpMultiplier);
	}

	const bool level_scaled = RuleI(AA, LevelBasedPointsPerLevel) > 0;
	const bool progression = exp_source == ExpSource::Quest || exp_source == ExpSource::Task;
	const uint64 level_award = AAProgression::LevelShare(award, m_epp.perAA);
	if (level_scaled) {
		aaexp = progression ? CalculateLevelBasedAAExp(award, level_award) : 0;
	} else if (m_epp.perAA > 0 || progression) {
		// Legacy AA-only modifiers remain available when level scaling is disabled.
		aaexp = RuleR(Character, AAExpMultiplier) > 0 ? static_cast<uint64>(aaexp * RuleR(Character, AAExpMultiplier)) : 0;
		if (RuleB(Character, EnableCharacterEXPMods)) {
			aaexp *= zone->GetAAEXPModifier(this);
		}
	} else {
		aaexp = 0;
	}
	SetEXP(exp_source, GetEXP() + level_award, FinalizeAAExperience(aaexp, level_scaled));
}

void Group::SplitExp(ExpSource exp_source, const uint64 exp, Mob* other) {
	if (other->CastToNPC()->MerchantType != 0) {
		return;
	}

	if (other->GetOwner() && other->GetOwner()->IsClient()) {
		return;
	}

	const auto member_count = GroupCount();
	if (!member_count) {
		return;
	}

	auto       group_experience = exp;
	const auto highest_level    = GetHighestLevel();

	auto group_modifier = 1.0f;
	if (RuleB(Character, EnableGroupMemberEXPModifier)) {
		if (EQ::ValueWithin(member_count, 2, 5)) {
			group_modifier = 1 + RuleR(Character, GroupMemberEXPModifier) * (member_count - 1); // 2 = 1.2x, 3 = 1.4x, 4 = 1.6x, 5 = 1.8x
		} else if (member_count == 6) {
			group_modifier = RuleR(Character, FullGroupEXPModifier);
		}
	}

	if (EQ::ValueWithin(member_count, 2, 6)) {
		if (RuleB(Character, EnableGroupEXPModifier)) {
			group_experience += static_cast<uint64>(
				static_cast<float>(exp) *
				group_modifier *
				RuleR(Character, GroupExpMultiplier)
			);
		} else {
			group_experience += static_cast<uint64>(
				static_cast<float>(exp) *
				group_modifier
			);
		}
	}

	const uint8 consider_level = Mob::GetLevelCon(highest_level, other->GetLevel());
	if (consider_level == ConsiderColor::Gray) {
		return;
	}

	for (const auto& m : members) {
		if (m && m->IsClient()) {
			const int32 diff     = m->GetLevel() - highest_level;
			int32       max_diff = -(m->GetLevel() * 15 / 10 - m->GetLevel());

			if (max_diff > -5) {
				max_diff = -5;
			}

			if (diff >= max_diff) {
				const uint64 tmp  = (m->GetLevel() + 3) * (m->GetLevel() + 3) * 75 * 35 / 10;
				const uint64 tmp2 = group_experience / member_count;
				m->CastToClient()->AddEXP(exp_source, tmp < tmp2 ? tmp : tmp2, consider_level, false, other->CastToNPC());
			}
		}
	}
}

void Raid::SplitExp(ExpSource exp_source, const uint64 exp, Mob* other) {
	if (other->CastToNPC()->MerchantType != 0) {
		return;
	}

	if (other->GetOwner() && other->GetOwner()->IsClient()) {
		return;
	}

	const auto member_count = RaidCount();
	if (!member_count) {
		return;
	}

	auto       raid_experience = exp;
	const auto highest_level   = GetHighestLevel();

	if (RuleB(Character, EnableRaidEXPModifier)) {
		raid_experience = static_cast<uint64>(static_cast<float>(raid_experience) *	(1.0f - RuleR(Character, RaidExpMultiplier)));
	}

	raid_experience = static_cast<uint64>(static_cast<float>(raid_experience) * RuleR(Character, FinalRaidExpMultiplier));

	const auto consider_level = Mob::GetLevelCon(highest_level, other->GetLevel());
	if (consider_level == ConsiderColor::Gray) {
		return;
	}

	uint32 member_modifier = 1;
	if (RuleB(Character, EnableRaidMemberEXPModifier)) {
		member_modifier = member_count;
	}

	for (const auto& m : members) {
		if (m.member && !m.is_bot) {
			const int32 diff     = m.member->GetLevel() - highest_level;
			int32       max_diff = -(m.member->GetLevel() * 15 / 10 - m.member->GetLevel());

			if (max_diff > -5) {
				max_diff = -5;
			}

			if (diff >= max_diff) {
				const uint64 tmp  = (m.member->GetLevel() + 3) * (m.member->GetLevel() + 3) * 75 * 35 / 10;
				const uint64 tmp2 = (raid_experience / member_modifier) + 1;
				m.member->AddEXP(exp_source, tmp < tmp2 ? tmp : tmp2, consider_level, false, other->CastToNPC());
			}
		}
	}
}

void Client::SetLeadershipEXP(uint64 group_exp, uint64 raid_exp) {
	while(group_exp >= GROUP_EXP_PER_POINT) {
		group_exp -= GROUP_EXP_PER_POINT;
		m_pp.group_leadership_points++;
		MessageString(Chat::LeaderShip, GAIN_GROUP_LEADERSHIP_POINT);
	}
	while(raid_exp >= RAID_EXP_PER_POINT) {
		raid_exp -= RAID_EXP_PER_POINT;
		m_pp.raid_leadership_points++;
		MessageString(Chat::LeaderShip, GAIN_RAID_LEADERSHIP_POINT);
	}

	m_pp.group_leadership_exp = group_exp;
	m_pp.raid_leadership_exp = raid_exp;

	SendLeadershipEXPUpdate();
}

void Client::AddLeadershipEXP(uint64 group_exp, uint64 raid_exp) {
	SetLeadershipEXP(GetGroupEXP() + group_exp, GetRaidEXP() + raid_exp);
}

void Client::SendLeadershipEXPUpdate() {
	auto outapp = new EQApplicationPacket(OP_LeadershipExpUpdate, sizeof(LeadershipExpUpdate_Struct));
	LeadershipExpUpdate_Struct* eu = (LeadershipExpUpdate_Struct *) outapp->pBuffer;

	eu->group_leadership_exp = m_pp.group_leadership_exp;
	eu->group_leadership_points = m_pp.group_leadership_points;
	eu->raid_leadership_exp = m_pp.raid_leadership_exp;
	eu->raid_leadership_points = m_pp.raid_leadership_points;

	FastQueuePacket(&outapp);
}

uint8 Client::GetCharMaxLevelFromQGlobal() {
	auto char_cache = GetQGlobals();

	std::list<QGlobal> global_map;

	const uint32 zone_id = zone ? zone->GetZoneID() : 0;

	if (char_cache) {
		QGlobalCache::Combine(global_map, char_cache->GetBucket(), 0, CharacterID(), zone_id);
	}

	for (const auto& global : global_map) {
		if (global.name == "CharMaxLevel") {
			if (Strings::IsNumber(global.value)) {
				return static_cast<uint8>(Strings::ToUnsignedInt(global.value));
			}
		}
	}

	return 0;
}

uint8 Client::GetCharMaxLevelFromBucket()
{
	DataBucketKey k = GetScopedBucketKeys();
	k.key = "CharMaxLevel";

	auto b = DataBucket::GetData(&database, k);
	if (!b.value.empty()) {
		if (Strings::IsNumber(b.value)) {
			return static_cast<uint8>(Strings::ToUnsignedInt(b.value));
		}
	}

	return 0;
}

uint32 Client::GetRequiredAAExperience() {
#ifdef LUA_EQEMU
	uint32 lua_ret = 0;
	bool ignoreDefault = false;
	lua_ret = LuaParser::Instance()->GetRequiredAAExperience(this, ignoreDefault);

	if (ignoreDefault) {
		return lua_ret;
	}
#endif

	return RuleI(AA, ExpPerPoint);
}
