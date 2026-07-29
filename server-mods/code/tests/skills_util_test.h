/*	EQEMu: Everquest Server Emulator
	Copyright (C) 2001-2014 EQEMu Development Team (http://eqemulator.net)

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

#pragma once

#include "common/skill_caps.h"
#include "common/skills.h"
#include "cppunit/cpptest.h"

class SkillsUtilsTest: public Test::Suite {
	typedef void(SkillsUtilsTest::*TestFunction)(void);
public:
	SkillsUtilsTest() {
		TEST_ADD(SkillsUtilsTest::IsTradeskill);
		TEST_ADD(SkillsUtilsTest::IsSpecializedSkill);
		TEST_ADD(SkillsUtilsTest::FindFirstTrainableLevel);
		TEST_ADD(SkillsUtilsTest::SkillAcquisitionPolicy);
		TEST_ADD(SkillsUtilsTest::ShouldSeedAtNativeUnlock);
		TEST_ADD(SkillsUtilsTest::CollectNativeSkillSeeds);
		TEST_ADD(SkillsUtilsTest::ResolveHeldSkillEligibility);
	}

	~SkillsUtilsTest() {
	}

	private:
	void IsTradeskill() {
		TEST_ASSERT(EQ::skills::IsTradeskill(EQ::skills::SkillPottery));
		TEST_ASSERT(!EQ::skills::IsTradeskill(EQ::skills::SkillParry));
	}

	void IsSpecializedSkill() {
		TEST_ASSERT(EQ::skills::IsSpecializedSkill(EQ::skills::SkillSpecializeConjuration));
		TEST_ASSERT(!EQ::skills::IsSpecializedSkill(EQ::skills::SkillConjuration))
	}

	void FindFirstTrainableLevel() {
		auto has_cap = [](uint8 level) { return level == 5 || level == 10; };

		TEST_ASSERT_EQUALS(SkillCaps::FindFirstTrainableLevel(4, has_cap), static_cast<uint8>(0));
		TEST_ASSERT_EQUALS(SkillCaps::FindFirstTrainableLevel(5, has_cap), static_cast<uint8>(5));
		TEST_ASSERT_EQUALS(SkillCaps::FindFirstTrainableLevel(75, has_cap), static_cast<uint8>(5));
	}

	void SkillAcquisitionPolicy() {
		using EQ::skills::SkillAcquisition;

		TEST_ASSERT(
			EQ::skills::GetSkillAcquisition(EQ::skills::SkillRoundKick) ==
				SkillAcquisition::AutoGrantAtNativeUnlock
		);
		TEST_ASSERT(
			EQ::skills::GetSkillAcquisition(EQ::skills::SkillAlchemy) ==
				SkillAcquisition::AutoGrantAtNativeUnlock
		);
		TEST_ASSERT(
			EQ::skills::GetSkillAcquisition(EQ::skills::SkillMakePoison) ==
				SkillAcquisition::AutoGrantAtNativeUnlock
		);
		TEST_ASSERT(
			EQ::skills::GetSkillAcquisition(EQ::skills::SkillResearch) ==
				SkillAcquisition::AutoGrantAtNativeUnlock
		);
		TEST_ASSERT(
			EQ::skills::GetSkillAcquisition(EQ::skills::SkillTinkering) ==
				SkillAcquisition::StockAcquisition
		);
		TEST_ASSERT(
			EQ::skills::GetSkillAcquisition(EQ::skills::SkillBaking) ==
				SkillAcquisition::StockAcquisition
		);

		for (int skill_id = 0; skill_id < EQ::skills::SkillCount; ++skill_id) {
			TEST_ASSERT(
				EQ::skills::GetSkillAcquisition(
					static_cast<EQ::skills::SkillType>(skill_id)
				) != SkillAcquisition::Unclassified
			);
		}
	}

	void ShouldSeedAtNativeUnlock() {
		using EQ::skills::SkillRoundKick;

		TEST_ASSERT(!EQ::skills::ShouldSeedAtNativeUnlock(SkillRoundKick, 0, 4, 5, 30));
		TEST_ASSERT(EQ::skills::ShouldSeedAtNativeUnlock(SkillRoundKick, 0, 5, 5, 30));
		TEST_ASSERT(EQ::skills::ShouldSeedAtNativeUnlock(SkillRoundKick, 0, 50, 5, 200));
		TEST_ASSERT(!EQ::skills::ShouldSeedAtNativeUnlock(SkillRoundKick, 1, 50, 5, 200));
		TEST_ASSERT(!EQ::skills::ShouldSeedAtNativeUnlock(SkillRoundKick, 200, 50, 5, 200));
		TEST_ASSERT(!EQ::skills::ShouldSeedAtNativeUnlock(SkillRoundKick, 0, 50, 0, 200));
		TEST_ASSERT(!EQ::skills::ShouldSeedAtNativeUnlock(SkillRoundKick, 0, 50, 5, 0));
		TEST_ASSERT(!EQ::skills::ShouldSeedAtNativeUnlock(
			EQ::skills::SkillTinkering,
			0,
			50,
			25,
			200
		));
	}

	void CollectNativeSkillSeeds() {
		using EQ::skills::NativeSkillSeedCandidate;
		using EQ::skills::SkillBash;
		using EQ::skills::SkillFlyingKick;
		using EQ::skills::SkillMakePoison;
		using EQ::skills::SkillRoundKick;
		using EQ::skills::SkillTinkering;

		const std::vector<NativeSkillSeedCandidate> candidates = {
			{SkillRoundKick, 0, 5, 30},
			{SkillTinkering, 0, 1, 200},
			{SkillBash, 1, 1, 25},
			{SkillFlyingKick, 0, 30, 100},
			{SkillMakePoison, 0, 20, 75}
		};

		auto seeds = EQ::skills::CollectNativeSkillSeeds(candidates, 19);
		TEST_ASSERT_EQUALS(seeds.size(), static_cast<size_t>(1));
		TEST_ASSERT(seeds[0] == SkillRoundKick);

		seeds = EQ::skills::CollectNativeSkillSeeds(candidates, 20);
		TEST_ASSERT_EQUALS(seeds.size(), static_cast<size_t>(2));
		TEST_ASSERT(seeds[0] == SkillRoundKick);
		TEST_ASSERT(seeds[1] == SkillMakePoison);
	}

	void ResolveHeldSkillEligibility() {
		const std::vector<uint8> held_classes = {Class::Cleric, Class::Monk, Class::Monk, 0, 99};
		auto result = SkillCaps::ResolveHeldSkillEligibility(
			held_classes,
			[](uint8 class_id) {
				if (class_id == Class::Cleric) {
					return static_cast<uint16>(75);
				}
				if (class_id == Class::Monk) {
					return static_cast<uint16>(200);
				}
				return static_cast<uint16>(500);
			},
			[](uint8 class_id) {
				if (class_id == Class::Cleric) {
					return static_cast<uint8>(10);
				}
				if (class_id == Class::Monk) {
					return static_cast<uint8>(5);
				}
				return static_cast<uint8>(1);
			}
		);

		TEST_ASSERT_EQUALS(result.current_cap, static_cast<uint16>(200));
		TEST_ASSERT_EQUALS(result.unlock_level, static_cast<uint8>(5));

		result = SkillCaps::ResolveHeldSkillEligibility(
			{0, 99},
			[](uint8) { return static_cast<uint16>(500); },
			[](uint8) { return static_cast<uint8>(1); }
		);
		TEST_ASSERT_EQUALS(result.current_cap, static_cast<uint16>(0));
		TEST_ASSERT_EQUALS(result.unlock_level, static_cast<uint8>(0));
	}
};
