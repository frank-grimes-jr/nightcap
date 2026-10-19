/*	EQEMu: Everquest Server Emulator
Copyright (C) 2001-2016 EQEMu Development Team (http://eqemulator.net)

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

#include "common/types.h"
#include "aa.h"

#include "common/classes.h"
#include "common/nightcap_aa_policy.h"
#include "common/eq_packet_structs.h"
#include "common/eqemu_logsys.h"
#include "common/events/player_event_logs.h"
#include "common/races.h"
#include "common/skill_caps.h"
#include "common/repositories/aa_ability_repository.h"
#include "common/repositories/aa_rank_effects_repository.h"
#include "common/repositories/aa_rank_prereqs_repository.h"
#include "common/repositories/aa_ranks_repository.h"
#include "common/repositories/character_alternate_abilities_repository.h"
#include "common/spdat.h"
#include "common/strings.h"
#include "zone/bot.h"
#include "zone/client.h"
#include "zone/corpse.h"
#include "zone/groups.h"
#include "zone/mob.h"
#include "zone/queryserv.h"
#include "zone/quest_parser_collection.h"
#include "zone/raids.h"
#include "zone/string_ids.h"
#include "zone/titles.h"
#include "zone/worldserver.h"
#include "zone/zonedb.h"

extern WorldServer worldserver;
extern QueryServ* QServ;

// ponytail: loads class2/class3 from character_multiclass so non-primary-class AAs
// show in the AA window. Called on every zone-in so selection changes take effect
// after a zone. Upgrade path: cache invalidation if we add an in-zone reclass command.
void Client::LoadMulticlassMask() {
	// Bit format MUST match the in-memory ability->classes, which is loaded as
	// (db_classes << 1) â€” i.e. bit N = class N ("EQ client format"). The old
	// (1 << (GetClass()-1)) mask was off by one bit against that: every character
	// was granted the AAs of class_id-1 instead of their own (the root cause of
	// the recurring vanish/wrong-class-AA bugs).
	m_multiclass_mask = (1 << GetClass());

	auto results = database.QueryDatabase(
		StringFormat("SELECT class2, class3 FROM character_multiclass WHERE character_id = %u", CharacterID())
	);

	if (!results.Success() || results.RowCount() == 0) {
		return;
	}

	auto row = results.begin();
	m_class2 = row[0] ? Strings::ToUnsignedInt(row[0]) : 0;
	m_class3 = row[1] ? Strings::ToUnsignedInt(row[1]) : 0;
	if (m_class2 > 0) m_multiclass_mask |= (1 << m_class2);
	if (m_class3 > 0) m_multiclass_mask |= (1 << m_class3);
}

void Client::SetMulticlassSlot(int slot, int class_id) {
	if (!m_multiclass_state_valid || slot < 2 || slot > 3 || class_id < 0 || class_id > 16) { return; }
	if (!class_id) { ReleaseMulticlassSlot(slot); return; }
	const auto selected = slot == 2 ? m_class2 : m_class3;
	if (selected == class_id) { return; }
	if (selected) {
		Message(Chat::Red, "Release the current discipline before selecting another class.");
		return;
	}
	if (class_id == GetClass()) {
		Message(Chat::Red, "You cannot select your primary class as an additional class.");
		return;
	}
	// prevent same class in both extra slots
	uint8 other = (slot == 2) ? m_class3 : m_class2;
	if (class_id != 0 && other == class_id) {
		Message(Chat::Red, "That class is already assigned to your other training slot.");
		return;
	}

	const char *col = (slot == 2) ? "class2" : "class3";
	auto check = database.QueryDatabase(fmt::format(
		"SELECT COALESCE(class2,0),COALESCE(class3,0) FROM character_multiclass WHERE character_id={}", CharacterID()), false);
	if (!check.Success() || check.RowCount() > 1) { InvalidateMulticlassState(); return; }
	if (!check.RowCount()) {
		if (m_class2 || m_class3) { InvalidateMulticlassState(); return; }
		auto inserted = database.QueryDatabase(fmt::format(
			"INSERT INTO character_multiclass (character_id,class2,class3) VALUES ({},{},{})",
			CharacterID(), slot == 2 ? class_id : 0, slot == 3 ? class_id : 0), false);
		if (!inserted.Success() || inserted.RowsAffected() != 1) { InvalidateMulticlassState(); return; }
	} else {
		if (Strings::ToUnsignedInt(check.begin()[0]) != m_class2 || Strings::ToUnsignedInt(check.begin()[1]) != m_class3) {
			InvalidateMulticlassState(); return;
		}
		auto changed = database.QueryDatabase(fmt::format(
			"UPDATE character_multiclass SET {}={} WHERE character_id={} AND COALESCE(class2,0)={} AND COALESCE(class3,0)={}",
			col, class_id, CharacterID(), m_class2, m_class3), false);
		if (!changed.Success() || changed.RowsAffected() != 1) { InvalidateMulticlassState(); return; }
	}

	ReconcileMulticlassSkills();
}

void Mob::TemporaryPets(uint16 spell_id, Mob *targ, const char *name_override, uint32 duration_override, bool followme, bool sticktarg, uint16 *eye_id) {

	//It might not be a bad idea to put these into the database, eventually..

	//Dook- swarms and wards

	// do nothing if it's a corpse
	if (targ != nullptr && targ->IsCorpse())
		return;

	// yep, even these need pet power!
	int act_power = 0;

	if (IsOfClientBot()) {
		act_power = GetFocusEffect(focusPetPower, spell_id);
		if (IsClient()) {
			act_power = CastToClient()->GetFocusEffect(focusPetPower, spell_id);
		}
	}

	PetRecord record;
	if (!content_db.GetPoweredPetEntry(spells[spell_id].teleport_zone, act_power, &record))
	{
		LogError("Unknown swarm pet spell id: {}, check pets table", spell_id);
		Message(Chat::Red, "Unable to find data for pet %s", spells[spell_id].teleport_zone);
		return;
	}

	SwarmPet_Struct pet;
	pet.count = 1;
	pet.duration = 1;

	for (int x = 0; x < MAX_SWARM_PETS; x++)
	{
		if (spells[spell_id].effect_id[x] == SpellEffect::TemporaryPets)
		{
			pet.count = spells[spell_id].base_value[x];
			pet.duration = spells[spell_id].max_value[x];
		}
	}

	pet.duration += GetFocusEffect(focusSwarmPetDuration, spell_id) / 1000;

	pet.npc_id = record.npc_type;

	NPCType *made_npc = nullptr;

	const NPCType *npc_type = content_db.LoadNPCTypesData(pet.npc_id);
	if (npc_type == nullptr) {
		//log write
		LogError("Unknown npc type for swarm pet spell id: [{}]", spell_id);
		Message(0, "Unable to find pet!");
		return;
	}

	if (name_override != nullptr) {
		//we have to make a custom NPC type for this name change
		made_npc = new NPCType;
		memcpy(made_npc, npc_type, sizeof(NPCType));
		strcpy(made_npc->name, name_override);
		npc_type = made_npc;
	}

	int summon_count = 0;
	summon_count = pet.count;

	if (summon_count > MAX_SWARM_PETS)
		summon_count = MAX_SWARM_PETS;

	static const glm::vec2 swarmPetLocations[MAX_SWARM_PETS] = {
		glm::vec2(5, 5), glm::vec2(-5, 5), glm::vec2(5, -5), glm::vec2(-5, -5),
		glm::vec2(10, 10), glm::vec2(-10, 10), glm::vec2(10, -10), glm::vec2(-10, -10),
		glm::vec2(8, 8), glm::vec2(-8, 8), glm::vec2(8, -8), glm::vec2(-8, -8)
	};

	NPC* swarm_pet_npc = nullptr;

	while (summon_count > 0) {
		int pet_duration = pet.duration;
		if (duration_override > 0)
			pet_duration = duration_override;

		//this is a little messy, but the only way to do it right
		//it would be possible to optimize out this copy for the last pet, but oh well
		NPCType *npc_dup = nullptr;
		if (made_npc != nullptr) {
			npc_dup = new NPCType;
			memcpy(npc_dup, made_npc, sizeof(NPCType));
		}

		swarm_pet_npc = new NPC(
			(npc_dup != nullptr) ? npc_dup : npc_type,	//make sure we give the NPC the correct data pointer
			0,
			GetPosition() + glm::vec4(swarmPetLocations[summon_count], 0.0f, 0.0f),
			GravityBehavior::Water);

		if (followme)
			swarm_pet_npc->SetFollowID(GetID());

		if (!swarm_pet_npc->GetSwarmInfo()) {
			auto nSI = new SwarmPet;
			swarm_pet_npc->SetSwarmInfo(nSI);
			swarm_pet_npc->GetSwarmInfo()->duration = new Timer(pet_duration * 1000);
		}
		else {
			swarm_pet_npc->GetSwarmInfo()->duration->Start(pet_duration * 1000);
		}

		swarm_pet_npc->StartSwarmTimer(pet_duration * 1000);

		//removing this prevents the pet from attacking
		swarm_pet_npc->GetSwarmInfo()->owner_id = GetID();

		//give the pets somebody to "love"
		if (targ != nullptr) {
			swarm_pet_npc->AddToHateList(targ, 1000, 1000);
			if (RuleB(Spells, SwarmPetTargetLock) || sticktarg) {
				swarm_pet_npc->GetSwarmInfo()->target = targ->GetID();
				swarm_pet_npc->SetPetTargetLockID(targ->GetID());
				swarm_pet_npc->SetSpecialAbility(SpecialAbility::AggroImmunity, 1);
			}
			else {
				swarm_pet_npc->GetSwarmInfo()->target = 0;
			}
		}

		//we allocated a new NPC type object, give the NPC ownership of that memory
		if (npc_dup != nullptr)
			swarm_pet_npc->GiveNPCTypeData(npc_dup);

		entity_list.AddNPC(swarm_pet_npc, true, true);
		summon_count--;
	}

	if (swarm_pet_npc && IsClient() && eye_id != nullptr) {
		*eye_id = swarm_pet_npc->GetID();
	}

	//the target of these swarm pets will take offense to being cast on...
	if (targ != nullptr)
		targ->AddToHateList(this, 1, 0);

	// The other pointers we make are handled elsewhere.
	delete made_npc;
}

void Mob::TypesTemporaryPets(uint32 typesid, Mob *targ, const char *name_override, uint32 duration_override, bool followme, bool sticktarg) {

	SwarmPet_Struct pet;
	pet.count = 1;
	pet.duration = 1;

	pet.npc_id = typesid;

	NPCType *made_npc = nullptr;

	const NPCType *npc_type = content_db.LoadNPCTypesData(typesid);
	if(npc_type == nullptr) {
		//log write
		LogError("Unknown npc type for swarm pet type id: [{}]", typesid);
		Message(0,"Unable to find pet!");
		return;
	}

	if(name_override != nullptr) {
		//we have to make a custom NPC type for this name change
		made_npc = new NPCType;
		memcpy(made_npc, npc_type, sizeof(NPCType));
		strcpy(made_npc->name, name_override);
		npc_type = made_npc;
	}

	int summon_count = 0;
	summon_count = pet.count;

	static const glm::vec2 swarmPetLocations[MAX_SWARM_PETS] = {
		glm::vec2(5, 5), glm::vec2(-5, 5), glm::vec2(5, -5), glm::vec2(-5, -5),
		glm::vec2(10, 10), glm::vec2(-10, 10), glm::vec2(10, -10), glm::vec2(-10, -10),
		glm::vec2(8, 8), glm::vec2(-8, 8), glm::vec2(8, -8), glm::vec2(-8, -8)
	};

	while(summon_count > 0) {
		int pet_duration = pet.duration;
		if(duration_override > 0)
			pet_duration = duration_override;

		//this is a little messy, but the only way to do it right
		//it would be possible to optimize out this copy for the last pet, but oh well
		NPCType *npc_dup = nullptr;
		if(made_npc != nullptr) {
			npc_dup = new NPCType;
			memcpy(npc_dup, made_npc, sizeof(NPCType));
		}

		NPC* swarm_pet_npc = new NPC(
				(npc_dup!=nullptr)?npc_dup:npc_type,	//make sure we give the NPC the correct data pointer
				0,
				GetPosition() + glm::vec4(swarmPetLocations[summon_count], 0.0f, 0.0f),
				GravityBehavior::Water);

		if (followme)
			swarm_pet_npc->SetFollowID(GetID());

		if(!swarm_pet_npc->GetSwarmInfo()){
			auto nSI = new SwarmPet;
			swarm_pet_npc->SetSwarmInfo(nSI);
			swarm_pet_npc->GetSwarmInfo()->duration = new Timer(pet_duration*1000);
		}
		else {
			swarm_pet_npc->GetSwarmInfo()->duration->Start(pet_duration*1000);
		}

		swarm_pet_npc->StartSwarmTimer(pet_duration * 1000);

		//removing this prevents the pet from attacking
		swarm_pet_npc->GetSwarmInfo()->owner_id = GetID();

		//give the pets somebody to "love"
		if(targ != nullptr){
			swarm_pet_npc->AddToHateList(targ, 1000, 1000);

			if (RuleB(Spells, SwarmPetTargetLock) || sticktarg) {
				swarm_pet_npc->GetSwarmInfo()->target = targ->GetID();
				swarm_pet_npc->SetPetTargetLockID(targ->GetID());
				swarm_pet_npc->SetSpecialAbility(SpecialAbility::AggroImmunity, 1);
			}
			else {
				swarm_pet_npc->GetSwarmInfo()->target = 0;
			}
		}

		//we allocated a new NPC type object, give the NPC ownership of that memory
		if(npc_dup != nullptr)
			swarm_pet_npc->GiveNPCTypeData(npc_dup);

		entity_list.AddNPC(swarm_pet_npc, true, true);
		summon_count--;
	}

	// The other pointers we make are handled elsewhere.
	delete made_npc;
}

void Mob::WakeTheDead(uint16 spell_id, Corpse *corpse_to_use, Mob *tar, uint32 duration) {

	/*
		SPA 299 Wake The Dead, 'animateDead' should be temp pet, always spawns 1 pet from corpse, max value is duration
		SPA 306 Wake The Dead, 'animateDead#' should be temp pet, base is amount of pets from indivual corpses, max value is duration
		Max range for closet corpse is 250 units.
		TODO: Should use temp pets
	*/

	if (!corpse_to_use) {
		return;
	}

	SwarmPet_Struct pet;
	pet.count = 1;
	pet.duration = 1;

	//pet.duration += GetFocusEffect(focusSwarmPetDuration, spell_id) / 1000; //TODO: Does WTD use pet focus?

	pet.npc_id = WAKE_THE_DEAD_NPCTYPEID;

	NPCType *made_npc = nullptr;

	const NPCType *npc_type = content_db.LoadNPCTypesData(WAKE_THE_DEAD_NPCTYPEID);
	if (npc_type == nullptr) {
		//log write
		LogError("Unknown npc type for 'Wake the Dead' swarm pet spell id: [{}]", spell_id);
		Message(0, "Unable to find pet!");
		return;
	}

	made_npc = new NPCType;
	memcpy(made_npc, npc_type, sizeof(NPCType));

	char NewName[64];
	sprintf(NewName, "%s`s Animated Corpse", GetCleanName());
	strcpy(made_npc->name, NewName);
	npc_type = made_npc;

	//combat stats
	made_npc->AC = ((GetLevel() * 7) + 550);
	made_npc->ATK = GetLevel();
	made_npc->max_dmg = (GetLevel() * 4) + 2;
	made_npc->min_dmg = 1;

	//base stats
	made_npc->current_hp = (GetLevel() * 55);
	made_npc->max_hp = (GetLevel() * 55);
	made_npc->STR = 85 + (GetLevel() * 3);
	made_npc->STA = 85 + (GetLevel() * 3);
	made_npc->DEX = 85 + (GetLevel() * 3);
	made_npc->AGI = 85 + (GetLevel() * 3);
	made_npc->INT = 85 + (GetLevel() * 3);
	made_npc->WIS = 85 + (GetLevel() * 3);
	made_npc->CHA = 85 + (GetLevel() * 3);
	made_npc->MR = 25;
	made_npc->FR = 25;
	made_npc->CR = 25;
	made_npc->DR = 25;
	made_npc->PR = 25;

	//level class and gender
	made_npc->level = GetLevel();
	made_npc->class_ = corpse_to_use->class_;
	made_npc->race = corpse_to_use->race;
	made_npc->gender = corpse_to_use->gender;
	made_npc->loottable_id = 0;

	//appearance
	made_npc->beard = corpse_to_use->beard;
	made_npc->beardcolor = corpse_to_use->beardcolor;
	made_npc->eyecolor1 = corpse_to_use->eyecolor1;
	made_npc->eyecolor2 = corpse_to_use->eyecolor2;
	made_npc->haircolor = corpse_to_use->haircolor;
	made_npc->hairstyle = corpse_to_use->hairstyle;
	made_npc->helmtexture = corpse_to_use->helmtexture;
	made_npc->luclinface = corpse_to_use->luclinface;
	made_npc->size = corpse_to_use->size;
	made_npc->texture = corpse_to_use->texture;

	//cast stuff.. based off of PEQ's if you want to change
	//it you'll have to mod this code, but most likely
	//most people will be using PEQ style for the first
	//part of their spell list; can't think of any smooth
	//way to do this
	//some basic combat mods here too since it's convienent
	switch (corpse_to_use->class_)
	{
	case Class::Cleric:
		made_npc->npc_spells_id = 1;
		break;
	case Class::Wizard:
		made_npc->npc_spells_id = 2;
		break;
	case Class::Necromancer:
		made_npc->npc_spells_id = 3;
		break;
	case Class::Magician:
		made_npc->npc_spells_id = 4;
		break;
	case Class::Enchanter:
		made_npc->npc_spells_id = 5;
		break;
	case Class::Shaman:
		made_npc->npc_spells_id = 6;
		break;
	case Class::Druid:
		made_npc->npc_spells_id = 7;
		break;
	case Class::Paladin:
		//SpecialAbility::TripleAttack
		strcpy(made_npc->special_abilities, "6,1");
		made_npc->current_hp = made_npc->current_hp * 150 / 100;
		made_npc->max_hp = made_npc->max_hp * 150 / 100;
		made_npc->npc_spells_id = 8;
		break;
	case Class::ShadowKnight:
		strcpy(made_npc->special_abilities, "6,1");
		made_npc->current_hp = made_npc->current_hp * 150 / 100;
		made_npc->max_hp = made_npc->max_hp * 150 / 100;
		made_npc->npc_spells_id = 9;
		break;
	case Class::Ranger:
		strcpy(made_npc->special_abilities, "7,1");
		made_npc->current_hp = made_npc->current_hp * 135 / 100;
		made_npc->max_hp = made_npc->max_hp * 135 / 100;
		made_npc->npc_spells_id = 10;
		break;
	case Class::Bard:
		strcpy(made_npc->special_abilities, "6,1");
		made_npc->current_hp = made_npc->current_hp * 110 / 100;
		made_npc->max_hp = made_npc->max_hp * 110 / 100;
		made_npc->npc_spells_id = 11;
		break;
	case Class::Beastlord:
		strcpy(made_npc->special_abilities, "7,1");
		made_npc->current_hp = made_npc->current_hp * 110 / 100;
		made_npc->max_hp = made_npc->max_hp * 110 / 100;
		made_npc->npc_spells_id = 12;
		break;
	case Class::Rogue:
		strcpy(made_npc->special_abilities, "7,1");
		made_npc->max_dmg = made_npc->max_dmg * 150 / 100;
		made_npc->current_hp = made_npc->current_hp * 110 / 100;
		made_npc->max_hp = made_npc->max_hp * 110 / 100;
		break;
	case Class::Monk:
		strcpy(made_npc->special_abilities, "7,1");
		made_npc->max_dmg = made_npc->max_dmg * 150 / 100;
		made_npc->current_hp = made_npc->current_hp * 135 / 100;
		made_npc->max_hp = made_npc->max_hp * 135 / 100;
		break;
	case Class::Warrior:
	case Class::Berserker:
		strcpy(made_npc->special_abilities, "7,1");
		made_npc->max_dmg = made_npc->max_dmg * 150 / 100;
		made_npc->current_hp = made_npc->current_hp * 175 / 100;
		made_npc->max_hp = made_npc->max_hp * 175 / 100;
		break;
	default:
		made_npc->npc_spells_id = 0;
		break;
	}

	made_npc->merchanttype = 0;
	made_npc->d_melee_texture1 = 0;
	made_npc->d_melee_texture2 = 0;


	int summon_count = 0;
	summon_count = pet.count;

	NPC* swarm_pet_npc = nullptr;
	//TODO: potenitally add support for multiple pets per corpse
	while (summon_count > 0) {
		int pet_duration = duration;

		NPCType *npc_dup = nullptr;
		if (made_npc != nullptr) {
			npc_dup = new NPCType;
			memcpy(npc_dup, made_npc, sizeof(NPCType));
		}

		swarm_pet_npc = new NPC(
			(npc_dup != nullptr) ? npc_dup : npc_type,
			0, corpse_to_use->GetPosition(),GravityBehavior::Water);

		swarm_pet_npc->SetFollowID(GetID());

		if (!swarm_pet_npc->GetSwarmInfo()) {
			auto nSI = new SwarmPet;
			swarm_pet_npc->SetSwarmInfo(nSI);
			swarm_pet_npc->GetSwarmInfo()->duration = new Timer(pet_duration * 1000);
		}
		else {
			swarm_pet_npc->GetSwarmInfo()->duration->Start(pet_duration * 1000);
		}

		swarm_pet_npc->StartSwarmTimer(pet_duration * 1000);

		//removing this prevents the pet from attacking
		swarm_pet_npc->GetSwarmInfo()->owner_id = GetID();

		//give the pets somebody to "love"
		if (tar != nullptr) {
			swarm_pet_npc->AddToHateList(tar, 10000, 1000);
			swarm_pet_npc->GetSwarmInfo()->target = 0;
		}

		//we allocated a new NPC type object, give the NPC ownership of that memory
		if (npc_dup != nullptr)
			swarm_pet_npc->GiveNPCTypeData(npc_dup);

		entity_list.AddNPC(swarm_pet_npc, true, true);
		summon_count--;
	}

	//the target of these swarm pets will take offense to being cast on...
	if (tar != nullptr)
		tar->AddToHateList(this, 1, 0);

	// The other pointers we make are handled elsewhere.
	delete made_npc;
}

void Client::ResetAA()
{
	// RefundAA now atomically removes refundable earned rows and preserves
	// grant-only survivors. A second deletion would undo that result.
	RefundAA();
}

void Client::ResetLeadershipAA()
{
	SendClearLeadershipAA();

	for (int slot_id = 0; slot_id < _maxLeaderAA; ++slot_id) {
		m_pp.leader_abilities.ranks[slot_id] = 0;
	}

	m_pp.group_leadership_points = 0;
	m_pp.raid_leadership_points  = 0;
	m_pp.group_leadership_exp    = 0;
	m_pp.raid_leadership_exp     = 0;

	database.DeleteCharacterLeadershipAbilities(CharacterID());
}

void Client::SendClearPlayerAA()
{
	auto outapp = new EQApplicationPacket(OP_ClearAA, 0);
	FastQueuePacket(&outapp);
}

void Client::SendClearLeadershipAA()
{
	auto outapp = new EQApplicationPacket(OP_ClearLeadershipAbilities, 0);
	FastQueuePacket(&outapp);
}

int Client::GroupLeadershipAAHealthEnhancement()
{
	if (IsRaidGrouped()) {
		int bonus = 0;
		Raid *raid = GetRaid();
		if (!raid)
			return 0;
		uint32 group_id = raid->GetGroup(this);
		if (group_id < 12 && raid->GroupCount(group_id) >= 3) {
			switch (raid->GetLeadershipAA(groupAAHealthEnhancement, group_id)) {
			case 1:
				bonus = 30;
				break;
			case 2:
				bonus = 60;
				break;
			case 3:
				bonus = 100;
				break;
			}
		}
		if (raid->RaidCount() >= 18) {
			switch (raid->GetLeadershipAA(raidAAHealthEnhancement)) {
			case 1:
				bonus += 30;
				break;
			case 2:
				bonus += 60;
				break;
			case 3:
				bonus += 100;
				break;
			}
		}
		return bonus;
	}

	Group *g = GetGroup();

	if(!g || (g->GroupCount() < 3))
		return 0;

	switch(g->GetLeadershipAA(groupAAHealthEnhancement))
	{
		case 0:
			return 0;
		case 1:
			return 30;
		case 2:
			return 60;
		case 3:
			return 100;
	}

	return 0;
}

int Client::GroupLeadershipAAManaEnhancement()
{
	if (IsRaidGrouped()) {
		int bonus = 0;
		Raid *raid = GetRaid();
		if (!raid)
			return 0;
		uint32 group_id = raid->GetGroup(this);
		if (group_id < 12 && raid->GroupCount(group_id) >= 3) {
			switch (raid->GetLeadershipAA(groupAAManaEnhancement, group_id)) {
			case 1:
				bonus = 30;
				break;
			case 2:
				bonus = 60;
				break;
			case 3:
				bonus = 100;
				break;
			}
		}
		if (raid->RaidCount() >= 18) {
			switch (raid->GetLeadershipAA(raidAAManaEnhancement)) {
			case 1:
				bonus += 30;
				break;
			case 2:
				bonus += 60;
				break;
			case 3:
				bonus += 100;
				break;
			}
		}
		return bonus;
	}

	Group *g = GetGroup();

	if(!g || (g->GroupCount() < 3))
		return 0;

	switch(g->GetLeadershipAA(groupAAManaEnhancement))
	{
		case 0:
			return 0;
		case 1:
			return 30;
		case 2:
			return 60;
		case 3:
			return 100;
	}

	return 0;
}

int Client::GroupLeadershipAAHealthRegeneration()
{
	if (IsRaidGrouped()) {
		int bonus = 0;
		Raid *raid = GetRaid();
		if (!raid)
			return 0;
		uint32 group_id = raid->GetGroup(this);
		if (group_id < 12 && raid->GroupCount(group_id) >= 3) {
			switch (raid->GetLeadershipAA(groupAAHealthRegeneration, group_id)) {
			case 1:
				bonus = 4;
				break;
			case 2:
				bonus = 6;
				break;
			case 3:
				bonus = 8;
				break;
			}
		}
		if (raid->RaidCount() >= 18) {
			switch (raid->GetLeadershipAA(raidAAHealthRegeneration)) {
			case 1:
				bonus += 4;
				break;
			case 2:
				bonus += 6;
				break;
			case 3:
				bonus += 8;
				break;
			}
		}
		return bonus;
	}

	Group *g = GetGroup();

	if(!g || (g->GroupCount() < 3))
		return 0;

	switch(g->GetLeadershipAA(groupAAHealthRegeneration))
	{
		case 0:
			return 0;
		case 1:
			return 4;
		case 2:
			return 6;
		case 3:
			return 8;
	}

	return 0;
}

int Client::GroupLeadershipAAOffenseEnhancement()
{
	if (IsRaidGrouped()) {
		int bonus = 0;
		Raid *raid = GetRaid();
		if (!raid)
			return 0;
		uint32 group_id = raid->GetGroup(this);
		if (group_id < 12 && raid->GroupCount(group_id) >= 3) {
			switch (raid->GetLeadershipAA(groupAAOffenseEnhancement, group_id)) {
			case 1:
				bonus = 10;
				break;
			case 2:
				bonus = 19;
				break;
			case 3:
				bonus = 28;
				break;
			case 4:
				bonus = 34;
				break;
			case 5:
				bonus = 40;
				break;
			}
		}
		if (raid->RaidCount() >= 18) {
			switch (raid->GetLeadershipAA(raidAAOffenseEnhancement)) {
			case 1:
				bonus += 10;
				break;
			case 2:
				bonus += 19;
				break;
			case 3:
				bonus += 28;
				break;
			case 4:
				bonus += 34;
				break;
			case 5:
				bonus += 40;
				break;
			}
		}
		return bonus;
	}

	Group *g = GetGroup();

	if(!g || (g->GroupCount() < 3))
		return 0;

	switch(g->GetLeadershipAA(groupAAOffenseEnhancement))
	{
		case 0:
			return 0;
		case 1:
			return 10;
		case 2:
			return 19;
		case 3:
			return 28;
		case 4:
			return 34;
		case 5:
			return 40;
	}
	return 0;
}

void Client::InspectBuffs(Client* Inspector, int Rank)
{
	// At some point the removed the restriction of being a group member for this to work
	// not sure when, but the way it's coded now, it wouldn't work with mobs.
	if (!Inspector || Rank == 0)
		return;

	auto outapp = new EQApplicationPacket(OP_InspectBuffs, sizeof(InspectBuffs_Struct));
	InspectBuffs_Struct *ib = (InspectBuffs_Struct *)outapp->pBuffer;

	uint32 buff_count = GetMaxTotalSlots();
	uint32 packet_index = 0;
	for (uint32 i = 0; i < buff_count; i++) {
		if (!IsValidSpell(buffs[i].spellid))
			continue;
		ib->spell_id[packet_index] = buffs[i].spellid;
		if (Rank > 1)
			ib->tics_remaining[packet_index] = spells[buffs[i].spellid].buff_duration_formula == DF_Permanent ? 0xFFFFFFFF : BuffDurationForClient(buffs[i].ticsremaining);
		packet_index++;
	}

	Inspector->FastQueuePacket(&outapp);
}

bool Client::RefundAA() {
	if (!HasValidEarnedAAState()) {
		return false;
	}
	auto earned = m_earned_aa_ranks;
	auto usable = aa_ranks;
	uint64 wallet = GetAAPoints();
	for (auto it = earned.begin(); it != earned.end();) {
		auto ability = zone->GetAlternateAdvancementAbilityByRank(it->first);
		auto rank = ability ? ability->GetRankByPointsSpent(it->second.first) : nullptr;
		if (!ability || ability->first_rank_id != it->first || !rank ||
			rank->current_value != it->second.first || rank->total_cost < 0) {
			InvalidateEarnedAAState();
			return false;
		}
		if (ability->grant_only || (ability->charges > 0 && it->second.second < 1)) {
			++it;
			continue;
		}
		wallet += rank->total_cost;
		if (wallet > UINT32_MAX) { return false; }
		usable.erase(ability->id);
		it = earned.erase(it);
	}
	if (!PersistEarnedAAState(std::move(earned), std::move(usable), static_cast<uint32>(wallet), m_epp.expended_aa)) {
		return false;
	}
	CalcBonuses();
	SendClearPlayerAA();
	SendAlternateAdvancementTable();
	SendAlternateAdvancementPoints();
	SendAlternateAdvancementStats();
	return true;
}

// All durable changes are staged against the session's earned ownership and
// retained classes. Expansion suspension must not erase a paid refund entitlement.
bool Client::ReleaseMulticlassSlot(int slot)
{
	if (!m_multiclass_state_valid || !HasValidEarnedAAState() || (slot != 2 && slot != 3)) { return false; }
	const auto primary = GetClass();
	if (primary < 1 || primary > 16 || m_class2 > 16 || m_class3 > 16 ||
		(m_class2 && m_class2 == primary) || (m_class3 && m_class3 == primary) ||
		(m_class2 && m_class2 == m_class3)) { return false; }
	if (!(slot == 2 ? m_class2 : m_class3)) { return false; }

	MulticlassReleaseState release = {};
	release.old_class2 = m_class2;
	release.old_class3 = m_class3;
	release.class2 = slot == 2 ? m_class3 : m_class2;
	release.class3 = 0;
	release.mask = (1u << primary) | (release.class2 ? 1u << release.class2 : 0);
	auto earned = m_earned_aa_ranks;
	auto usable = aa_ranks;
	uint64 wallet = GetAAPoints();
	for (auto it = earned.begin(); it != earned.end();) {
		auto ability = zone->GetAlternateAdvancementAbilityByRank(it->first);
		auto rank = ability ? ability->GetRankByPointsSpent(it->second.first) : nullptr;
		if (!ability || ability->first_rank_id != it->first || !rank ||
			rank->current_value != it->second.first || rank->total_cost < 0) {
			InvalidateMulticlassState();
			return false;
		}
		if (ability->classes & release.mask) { ++it; continue; }
		if (!ability->grant_only && (ability->charges < 1 || it->second.second > 0)) {
			wallet += rank->total_cost;
			if (wallet > UINT32_MAX) { return false; }
		}
		usable.erase(ability->id);
		it = earned.erase(it);
	}
	for (const auto &entry : EQ::skills::GetSkillTypeMap()) {
		const auto skill = entry.first;
		uint16 cap = SkillCaps::Instance()->GetSkillCap(primary, skill, GetLevel()).cap;
		if (release.class2) {
			const uint16 other_cap = SkillCaps::Instance()->GetSkillCap(release.class2, skill, GetLevel()).cap;
			cap = std::max(cap, other_cap);
		}
		const uint16 current = GetRawSkill(skill);
		release.skills.push_back({skill, current, std::min(current, cap)});
	}
	const auto refund = wallet - GetAAPoints();
	if (!PersistEarnedAAState(std::move(earned), std::move(usable), static_cast<uint32>(wallet), m_epp.expended_aa, &release)) {
		InvalidateMulticlassState();
		return false;
	}
	// Persistence published slots, raw skills, ownership and profile together.
	// No SetSkill/Save calls or second DB class read may follow the commit.
	RefreshClassPets();
	CalcBonuses();
	for (const auto &skill : release.skills) {
		if (skill.before == skill.after) { continue; }
		auto outapp = new EQApplicationPacket(OP_SkillUpdate, sizeof(SkillUpdate_Struct));
		auto update = reinterpret_cast<SkillUpdate_Struct *>(outapp->pBuffer);
		update->skillId = skill.skill;
		update->value = skill.after;
		QueuePacket(outapp);
		safe_delete(outapp);
	}
	SendClearPlayerAA();
	SendLoadedAlternateAdvancementTable();
	SendAlternateAdvancementPoints();
	SendAlternateAdvancementStats();
	LogInfo("[ReleaseMulticlassSlot] [{}] released slot [{}]: refunded [{}] AA points", CharacterID(), slot, refund);
	return true;
}

void Client::PurgeAfterClassRelease(uint8 released_class)
{
	LogError("Retired non-atomic class release called for [{}], class [{}]; deploy the matching multiclass plugin", CharacterID(), released_class);
	InvalidateMulticlassState();
}

SwarmPet::SwarmPet()
{
	target = 0;
	owner_id = 0;
	duration = nullptr;
}

SwarmPet::~SwarmPet()
{
	target = 0;
	owner_id = 0;
	safe_delete(duration);
}

Mob *SwarmPet::GetOwner()
{
	return entity_list.GetMobID(owner_id);
}

//New AA
bool Client::ReprojectEarnedAAs() {
	if (!HasValidEarnedAAState()) { return false; }
	UsableAAState usable;
	for (const auto& owned : m_earned_aa_ranks) {
		auto ability = zone->GetAlternateAdvancementAbilityByRank(owned.first);
		auto rank = ability ? ability->GetRankByPointsSpent(owned.second.first) : nullptr;
		if (!ability || ability->first_rank_id != owned.first || !rank ||
			rank->current_value != owned.second.first) {
			InvalidateEarnedAAState();
			return false;
		}
		const auto count = std::min(owned.second.first, static_cast<uint32>(ability->GetMaxLevel(this)));
		if (count) { usable[ability->id] = {count, owned.second.second}; }
	}
	if (usable.size() > MAX_PP_AA_ARRAY) {
		InvalidateEarnedAAState();
		return false;
	}
	// Preserve any session charge consumption before an ability becomes dormant.
	for (const auto& active : aa_ranks) {
		auto ability = zone->GetAlternateAdvancementAbility(active.first);
		auto owned = ability ? m_earned_aa_ranks.find(ability->first_rank_id) : m_earned_aa_ranks.end();
		if (owned != m_earned_aa_ranks.end()) {
			owned->second.second = active.second.second;
			const auto next = usable.find(active.first);
			if (next != usable.end()) { next->second.second = active.second.second; }
		}
	}
	aa_ranks = std::move(usable);
	memset(m_pp.aa_array, 0, sizeof(m_pp.aa_array));
	uint32 slot = 0;
	for (const auto& active : aa_ranks) {
		auto ability = zone->GetAlternateAdvancementAbility(active.first);
		m_pp.aa_array[slot].AA = ability->first_rank_id;
		m_pp.aa_array[slot].value = active.second.first;
		m_pp.aa_array[slot].charges = active.second.second;
		++slot;
	}
	return true;
}

void Client::SendAlternateAdvancementTable() {
	LoadMulticlassMask();
	if (!ReprojectEarnedAAs()) { return; }
	CalcBonuses();
	SendLoadedAlternateAdvancementTable();
	SendAlternateAdvancementPoints();
	SendAlternateAdvancementStats();
}

void Client::RefreshNightcapUI() {
	if (!zone || (m_nightcap_ui_enabled && !m_nightcap_ui_refresh_timer.Check())) { return; }
	m_nightcap_ui_refresh_timer.Start(3000);
	m_nightcap_ui_enabled = true;
	SendLoadedAlternateAdvancementTable();
}

void Client::SendLoadedAlternateAdvancementTable() {
	SendClearPlayerAA();
	// Versioned presentation snapshot; never changes AA eligibility or ownership.
	if (m_nightcap_ui_enabled) {
		if (++m_nightcap_ui_generation == 0) { ++m_nightcap_ui_generation; }
		Message(Chat::White, "[NCUI1]S|%u|%u|%u|%u|%u|%u|%u|%u|%s",
			m_nightcap_ui_generation, CharacterID(), zone->GetZoneID(), zone->GetInstanceID(),
			GetID(), GetClass(), GetClass2(), GetClass3(), GetCleanName());
	}
	for(auto &aa : zone->aa_abilities) {
		uint32 charges = 0;
		auto ranks = GetAA(aa.second->first_rank_id, &charges);
		if(ranks) {
			if(aa.second->GetMaxLevel(this) == ranks) {
				SendAlternateAdvancementRank(aa.first, ranks);
			} else {
				SendAlternateAdvancementRank(aa.first, ranks);
				SendAlternateAdvancementRank(aa.first, ranks + 1);
			}
		} else {
			SendAlternateAdvancementRank(aa.first, 1);
		}
	}
	SendAlternateAdvancementTimers();
	// The native AAExpUpdate handler rebuilds an already-open AA window.
	if (m_nightcap_ui_enabled) { SendAlternateAdvancementStats(); }
}

void Client::SendAlternateAdvancementRank(int aa_id, int level) {
	if(!zone)
		return;

	auto ability_rank = zone->GetAlternateAdvancementAbilityAndRank(aa_id, level);
	auto ability = ability_rank.first;
	auto rank = ability_rank.second;

	if(!ability) {
		return;
	}

	if(!(ability->classes & GetClassMask())) {
		return;
	}

	if(!CanUseAlternateAdvancementRank(rank)) {
		return;
	}
	const int cooldown_slot = GetAlternateAdvancementTimerSlot(ability->id);
	if (IsValidSpell(rank->spell) && (rank->effects.empty() || UseTogglePassiveHotkey(*rank)) && cooldown_slot < 0) {
		return;
	}

	int size = sizeof(AARankInfo_Struct) + (sizeof(AARankEffect_Struct) * rank->effects.size()) + (sizeof(AARankPrereq_Struct) * rank->prereqs.size());
	auto outapp = new EQApplicationPacket(OP_SendAATable, size);
	AARankInfo_Struct *aai = (AARankInfo_Struct*)outapp->pBuffer;

	// Publish the original mask, before the client visibility mask is reshaped.
	// List row data is rank->id, not ability->id. Send before the table row.
	if (m_nightcap_ui_enabled) {
		Message(Chat::White, "[NCUI1]A|%u|%u|%u|%u|%u|%u|%u",
			m_nightcap_ui_generation, CharacterID(), zone->GetZoneID(), zone->GetInstanceID(),
			GetID(), rank->id, ability->classes & 0x1fffe);
	}

	aai->id = rank->id;
	aai->upper_hotkey_sid = rank->upper_hotkey_sid;
	aai->lower_hotkey_sid = rank->lower_hotkey_sid;
	aai->title_sid = rank->title_sid;
	aai->desc_sid = rank->desc_sid;
	aai->cost = rank->cost;
	aai->seq = aa_id;
	aai->type = ability->type;
	aai->spell = rank->spell;
	aai->spell_type = cooldown_slot;
	aai->spell_refresh = rank->recast_time;
	// Multiclass client display: the client both hides AAs whose class list excludes
	// the character's class AND files them into tabs (Class/Archetype/General) from
	// that same list. The server already authorized this AA (CanUse via the multiclass
	// mask), so reshape the list purely for the client:
	//   - single-class AA (a secondary class's own AA) -> present as THIS character's
	//     class bit, so it files into the Class tab beside the native-class AAs.
	//   - multi-class AA (archetype/general) -> just OR our class bit in for visibility.
	// classes here is client format: bit N = class N (see loader, classes << 1)
	uint32 my_class_bit = 1 << GetClass();
	bool single_class = (ability->classes != 0) && ((ability->classes & (ability->classes - 1)) == 0);
	aai->classes = single_class ? my_class_bit : (ability->classes | my_class_bit);
	// Nightcap opens every allowed AA rank at character creation.
	aai->level_req = NightcapAA::RequiredLevel(rank->id, ability->id, rank->current_value, rank->expansion);
	aai->current_level = level;
	aai->max_level = ability->GetMaxLevel(this);
	aai->prev_id = rank->prev_id;

	if((rank->next && !CanUseAlternateAdvancementRank(rank->next)) || ability->charges > 0) {
		aai->next_id = -1;
	} else {
		aai->next_id = rank->next_id;
	}
	aai->total_cost = rank->total_cost;
	// Multiclass/all-AA server: the client hides AAs whose expansion it thinks is
	// not unlocked, ignoring the (full) expansion mask we send. Report expansion 0
	// so the client never hides a server-authorized AA on expansion grounds.
	// ponytail: blanket 0; if you ever want era-accurate AA labels, gate this.
	aai->expansion = 0;
	aai->category = ability->category;
	aai->charges = ability->charges;
	aai->grant_only = ability->grant_only;
	aai->total_effects = rank->effects.size();
	aai->total_prereqs = rank->prereqs.size();

	outapp->SetWritePosition(sizeof(AARankInfo_Struct));
	for(auto &effect : rank->effects) {
		outapp->WriteSInt32(effect.effect_id);
		outapp->WriteSInt32(effect.base_value);
		outapp->WriteSInt32(effect.limit_value);
		outapp->WriteSInt32(effect.slot);
	}

	for(auto &prereq : rank->prereqs) {
		outapp->WriteSInt32(prereq.first);
		outapp->WriteSInt32(prereq.second);
	}

	QueuePacket(outapp);
	safe_delete(outapp);
}

#include "../common/aa_recommendations.h"
#include "aa_recommendations.inc"

void Client::SendAlternateAdvancementStats() {
	SendAARecommendations();
	NormalizeAAAllocation();
	auto outapp = new EQApplicationPacket(OP_AAExpUpdate, sizeof(AltAdvStats_Struct));
	AltAdvStats_Struct *aps = (AltAdvStats_Struct *)outapp->pBuffer;
	aps->experience = (uint32)(((float)330.0f * (float)m_pp.expAA) / (float)GetRequiredAAExperience());
	aps->unspent = m_pp.aapoints;
	aps->percentage = m_epp.perAA;
	QueuePacket(outapp);
	safe_delete(outapp);
}

void Client::SendAlternateAdvancementPoints() {
	auto outapp = new EQApplicationPacket(OP_RespondAA, sizeof(AATable_Struct));
	AATable_Struct* aa2 = (AATable_Struct *)outapp->pBuffer;

	int i = 0;
	for(auto &aa : zone->aa_abilities) {
		uint32 charges = 0;
		auto ranks = GetAA(aa.second->first_rank_id, &charges);
		if(ranks) {
			AA::Rank *rank = aa.second->GetRankByPointsSpent(ranks);
			if(rank) {
				aa2->aa_list[i].AA = rank->id;
				aa2->aa_list[i].value = rank->total_cost;
				aa2->aa_list[i].charges = charges;
				i++;
			}
		}
	}


	aa2->aa_spent = GetSpentAA();
	QueuePacket(outapp);
	safe_delete(outapp);
}

// RoF2 stores exactly 100 AA clocks. Allocate from the full held-class catalog,
// not purchased/visible ranks: buying an AA must never renumber an active clock.
int Client::GetAlternateAdvancementTimerSlot(int family_id) {
	if (!zone || family_id < 0 || family_id >= 0x100000) { return -1; }
	std::set<int> families;
	for (const auto &entry : zone->aa_ranks) {
		const auto *rank = entry.second.get();
		const auto *ability = rank->base_ability;
		if (!ability || !(ability->classes & GetClassMask()) || !IsValidSpell(rank->spell) ||
			(!rank->effects.empty() && !UseTogglePassiveHotkey(*rank)) ||
			!NightcapAA::RequiredLevel(rank->id, ability->id, rank->current_value, rank->expansion)) {
			continue;
		}
		families.insert(ability->id);
	}
	if (families.size() > 100) { return -1; } // fail closed; never alias or index native memory
	const auto found = families.find(family_id);
	return found == families.end() ? -1 : static_cast<int>(std::distance(families.begin(), found));
}

// The public argument is a stable AA family ID. Only this boundary uses a wire slot.
void Client::SendAlternateAdvancementTimer(int family_id, int begin, int end) {
	const int slot = GetAlternateAdvancementTimerSlot(family_id);
	if (slot < 0) { return; }
	auto outapp = new EQApplicationPacket(OP_AAAction, sizeof(UseAA_Struct));
	auto *timer = reinterpret_cast<UseAA_Struct *>(outapp->pBuffer);
	timer->ability = slot;
	timer->begin = begin;
	timer->end = end;
	QueuePacket(outapp);
	safe_delete(outapp);
}

void Client::SendAlternateAdvancementTimers() {
	const uint32 now = static_cast<uint32>(time(nullptr));
	// Clear every native slot, including slots belonging to a released class.
	// (0,0) STARTS a native cooldown; (0,now) is the reset packet.
	auto outapp = new EQApplicationPacket(OP_AAAction, sizeof(UseAA_Struct));
	auto *timer = reinterpret_cast<UseAA_Struct *>(outapp->pBuffer);
	timer->begin = 0;
	timer->end = now;
	for (int slot = 0; slot < 100; ++slot) {
		timer->ability = slot;
		QueuePacket(outapp);
	}
	safe_delete(outapp);
	for (const auto &aa : aa_ranks) {
		auto pair = zone->GetAlternateAdvancementAbilityAndRank(aa.first, aa.second.first);
		auto *ability = pair.first;
		auto *rank = pair.second;
		if (!ability || !rank || !CanUseAlternateAdvancementRank(rank)) { continue; }
		const uint32 remaining = p_timers.GetRemainingTime(pTimerAAStart + ability->id);
		if (!remaining) { continue; }
		const int effective_reuse = rank->recast_time - GetAlternateAdvancementCooldownReduction(rank);
		// Native readiness subtracts its effective reuse from this start timestamp.
		// A future start preserves a migrated legacy wait longer than this AA's reuse.
		SendAlternateAdvancementTimer(ability->id, now + remaining - effective_reuse, now);
	}
}

void Client::ResetAlternateAdvancementTimer(int rank_id) {
	auto *rank = zone->GetAlternateAdvancementRank(rank_id);
	if (rank && rank->base_ability) {
		p_timers.Clear(&database, pTimerAAStart + rank->base_ability->id);
		SendAlternateAdvancementTimer(rank->base_ability->id, 0, time(nullptr));
	}
}

void Client::ResetAlternateAdvancementTimers() {
	std::vector<pTimerType> keys;
	for (const auto &entry : p_timers) {
		if (entry.first >= pTimerAAStart && entry.first <= pTimerAAEnd) {
			keys.push_back(entry.first);
		}
	}
	for (const auto key : keys) { p_timers.Clear(&database, key); }
	SendAlternateAdvancementTimers();
}

void Client::ResetOnDeathAlternateAdvancement() {
	for (const auto &aa : aa_ranks) {
		auto pair = zone->GetAlternateAdvancementAbilityAndRank(aa.first, aa.second.first);
		if (pair.first && pair.second && pair.first->reset_on_death) {
			p_timers.Clear(&database, pTimerAAStart + pair.first->id);
		}
	}
}

void Client::PurchaseAlternateAdvancementRank(int rank_id) {
	AA::Rank *rank = zone->GetAlternateAdvancementRank(rank_id);
	if(!rank) {
		return;
	}

	if(!rank->base_ability) {
		return;
	}

	if(!CanPurchaseAlternateAdvancementRank(rank, true, true)) {
		return;
	}

	FinishAlternateAdvancementPurchase(rank, false, true);
}

bool Client::GrantAlternateAdvancementAbility(int aa_id, int points, bool ignore_cost) {
	bool ret = false;
	for(int i = 1; i <= points; ++i) {
		auto ability_rank = zone->GetAlternateAdvancementAbilityAndRank(aa_id, i);
		auto ability = ability_rank.first;
		auto rank = ability_rank.second;

		if(!rank) {
			continue;
		}

		if(!rank->base_ability) {
			continue;
		}

		if(!CanPurchaseAlternateAdvancementRank(rank, !ignore_cost, false)) {
			continue;
		}

		if (FinishAlternateAdvancementPurchase(rank, ignore_cost, true)) {
			ret = true;
		} else if (!HasValidEarnedAAState()) {
			break;
		}
	}

	return ret;
}

bool Client::FinishAlternateAdvancementPurchase(AA::Rank *rank, bool ignore_cost, bool send_message) {
	// Callers retain their purchase/grant eligibility rules (including explicit
	// grant unlock levels). Never publish a new rank or spend session points
	// before canonical ownership and character counters commit together.
	if (!HasValidEarnedAAState() || !rank || !rank->base_ability ||
		rank->current_value < 1 || rank->cost < 0 || rank->total_cost < 0 ||
		!CanUseAlternateAdvancementRank(rank) || HasAlreadyPurchasedRank(rank) ||
		rank->current_value > rank->base_ability->GetMaxLevel(this)) {
		return false;
	}
	const auto ability = rank->base_ability;
	const auto rank_id = ability->first_rank_id;
	const int32 cost = ignore_cost ? 0 : rank->cost;
	if (cost > GetAAPoints() || (ability->charges && GetEarnedAACount(rank_id))) {
		return false;
	}
	auto earned = m_earned_aa_ranks;
	auto usable = aa_ranks;
	earned[rank_id] = {rank->current_value, ability->charges};
	usable[ability->id] = earned[rank_id];
	if (!PersistEarnedAAState(std::move(earned), std::move(usable), GetAAPoints() - cost, m_epp.expended_aa)) {
		return false;
	}
	if (send_message) {
		if (!ability->charges && rank->next) {
			SendAlternateAdvancementRank(ability->id, rank->next->current_value);
		}
		SendAlternateAdvancementPoints();
		SendAlternateAdvancementStats();
		SendAlternateAdvancementTimers();
	}

	if (PlayerEventLogs::Instance()->IsEventEnabled(PlayerEvent::AA_PURCHASE)) {
		auto e = PlayerEvent::AAPurchasedEvent{
			.aa_id = rank->id,
			.aa_cost = cost,
			.aa_previous_id = rank->prev_id,
			.aa_next_id = rank->next_id
		};

		RecordPlayerEventLog(PlayerEvent::AA_PURCHASE, e);
	}

	if (rank->prev) {
		if (send_message) {
			MessageString(
				Chat::Yellow,
				AA_IMPROVE,
				std::to_string(rank->title_sid).c_str(),
				std::to_string(rank->prev->current_value).c_str(),
				std::to_string(cost).c_str(),
				cost == 1 ? std::to_string(AA_POINT).c_str() : std::to_string(AA_POINTS).c_str()
			);
		}
	} else {
		if (send_message) {
			MessageString(
				Chat::Yellow,
				AA_GAIN_ABILITY,
				std::to_string(rank->title_sid).c_str(),
				std::to_string(cost).c_str(),
				cost == 1 ? std::to_string(AA_POINT).c_str() : std::to_string(AA_POINTS).c_str()
			);
		}
	}

	if (parse->PlayerHasQuestSub(EVENT_AA_BUY)) {
		const auto& export_string = fmt::format(
			"{} {} {} {}",
			cost,
			rank->id,
			rank->prev_id,
			rank->next_id
		);

		parse->EventPlayer(EVENT_AA_BUY, this, export_string, 0);
	}

	CalcBonuses();

	if (cost) {
		if (title_manager.IsNewAATitleAvailable(m_pp.aapoints_spent, GetBaseClass())) {
			NotifyNewTitlesAvailable();
		}
	}
	return true;
}

//need to rewrite this
void Client::IncrementAlternateAdvancementRank(int rank_id) {
	AA::Rank *rank = zone->GetAlternateAdvancementRank(rank_id);
	if(!rank) {
		return;
	}

	if(!rank->base_ability) {
		return;
	}

	int points = GetAA(rank_id);
	GrantAlternateAdvancementAbility(rank->base_ability->id, points + 1, true);
}

void Client::ActivateAlternateAdvancementAbility(int rank_id, int target_id) {
	if (!HasValidEarnedAAState()) {
		Message(Chat::Red, "Alternate advancement is temporarily unavailable. Please reconnect.");
		return;
	}
	AA::Rank *rank = zone->GetAlternateAdvancementRank(rank_id);

	if (!rank) {
		return;
	}

	AA::Ability *ability = rank->base_ability;
	if (!ability) {
		return;
	}

	if (!IsValidSpell(rank->spell)) {
		return;
	}

	if (!CanUseAlternateAdvancementRank(rank)) {
		return;
	}

	bool use_toggle_passive_hotkey = UseTogglePassiveHotkey(*rank);

	//make sure it is not a passive
	if (!rank->effects.empty() && !use_toggle_passive_hotkey) {
		return;
	}

	uint32 charges = 0;
	// We don't have the AA
	if (GetAA(rank_id, &charges) < static_cast<uint32>(rank->current_value))
		return;
	//if expendable make sure we have charges
	if (ability->charges > 0 && charges < 1)
		return;

	if (GetAlternateAdvancementTimerSlot(ability->id) < 0) {
		Message(Chat::Red, "This ability has no available cooldown slot. Please report this to a GM.");
		return;
	}
	//check cooldown
	if (!p_timers.Expired(&database, pTimerAAStart + ability->id, false)) {
		uint32 aaremain = p_timers.GetRemainingTime(pTimerAAStart + ability->id);
		uint32 aaremain_hr = aaremain / (60 * 60);
		uint32 aaremain_min = (aaremain / 60) % 60;
		uint32 aaremain_sec = aaremain % 60;

		if (aaremain_hr >= 1) {
			Message(Chat::Red, "You can use this ability again in %u hour(s) %u minute(s) %u seconds",
				aaremain_hr, aaremain_min, aaremain_sec);
		}
		else {
			Message(Chat::Red, "You can use this ability again in %u minute(s) %u seconds",
				aaremain_min, aaremain_sec);
		}

		return;
	}

	int timer_duration = rank->recast_time - GetAlternateAdvancementCooldownReduction(rank);
	if (timer_duration < 0) {
		timer_duration = 0;
	}

	if (!IsCastWhileInvisibleSpell(rank->spell))
		CommonBreakInvisible();

	if (spells[rank->spell].sneak && (!hidden || (hidden && (Timer::GetCurrentTime() - tmHidden) < 4000))) {
		MessageString(Chat::SpellFailure, SNEAK_RESTRICT);
		return;
	}
	//
	// Modern clients don't require pet targeted for AA casts that are ST_Pet
	if (spells[rank->spell].target_type == ST_Pet || spells[rank->spell].target_type == ST_SummonedPet)
		target_id = GetPetID();

	// extra handling for cast_not_standing spells
	if (!IsCastNotStandingSpell(rank->spell)) {
		if (GetAppearance() == eaSitting) // we need to stand!
			SetAppearance(eaStanding, false);

		if (GetAppearance() != eaStanding) {
			MessageString(Chat::SpellFailure, STAND_TO_CAST);
			return;
		}
	}

	if (use_toggle_passive_hotkey) {
		TogglePassiveAlternativeAdvancement(*rank, ability->id);
	}
	else {
		// Bards can cast instant cast AAs while they are casting or channeling item cast.
		if (GetClass() == Class::Bard && IsCasting() && spells[rank->spell].cast_time == 0) {
			if (!DoCastingChecksOnCaster(rank->spell, EQ::spells::CastingSlot::AltAbility)) {
				return;
			}

			if (!SpellFinished(rank->spell, entity_list.GetMob(target_id), EQ::spells::CastingSlot::AltAbility, spells[rank->spell].mana, -1, spells[rank->spell].resist_difficulty, false, -1,
				pTimerAAStart + ability->id, timer_duration, false, rank->id)) {
				return;
			}
		}
		else {
			if (!CastSpell(rank->spell, target_id, EQ::spells::CastingSlot::AltAbility, -1, -1, 0, -1, pTimerAAStart + ability->id, timer_duration, nullptr, rank->id)) {
				return;
			}
		}
	}
}

int Mob::GetAlternateAdvancementCooldownReduction(AA::Rank *rank_in) {
	if(!rank_in) {
		return 0;
	}

	AA::Ability *ability_in = rank_in->base_ability;
	if(!ability_in) {
		return 0;
	}

	int total_reduction = 0;
	for(auto &aa : aa_ranks) {
		auto ability_rank = zone->GetAlternateAdvancementAbilityAndRank(aa.first, aa.second.first);
		auto ability = ability_rank.first;
		auto rank = ability_rank.second;

		if(!ability) {
			continue;
		}

		for(auto &effect : rank->effects) {
			if(effect.effect_id == SpellEffect::HastenedAASkill && effect.limit_value == ability_in->id) {
				total_reduction += effect.base_value;
			}
		}
	}

	return total_reduction;
}

void Mob::ExpendAlternateAdvancementCharge(uint32 aa_id) {
	if (IsClient()) {
		auto ability = zone->GetAlternateAdvancementAbility(aa_id);
		auto client = CastToClient();
		if (ability && client->ExpendEarnedAACharge(ability->first_rank_id)) {
			client->CalcBonuses();
			client->SendAlternateAdvancementPoints();
		}
		return;
	}
	for (auto &iter : aa_ranks) {
		auto ability = zone->GetAlternateAdvancementAbility(iter.first);
		if (ability && aa_id == ability->id) {
			if (iter.second.second > 0) {
				iter.second.second -= 1;

				if (iter.second.second == 0) {
					aa_ranks.erase(iter.first);
				}
			}

			return;
		}
	}
}

bool ZoneDatabase::LoadAlternateAdvancement(Client *c) {
	// An in-place AA reload does not reload the character's point counters.
	// Once those may be untrusted, only a fresh client session may clear the
	// failure state; otherwise a later profile save could undo a committed change.
	if (!c->HasValidEarnedAAState()) {
		LogError("Refusing in-place AA recovery for [{}]; reconnect to reload ownership and counters", c->CharacterID());
		return false;
	}
	// Preserve the session on a read failure; an empty result must be distinguishable
	// from a failed ownership query before any later save is allowed.
	auto rows = database.QueryDatabase(fmt::format(
		"SELECT aa_id, aa_value, charges FROM character_alternate_abilities WHERE id={} ORDER BY aa_id",
		c->CharacterID()));
	if (!rows.Success()) {
		c->InvalidateEarnedAAState();
		return false;
	}
	c->ClearAAs();
	c->BeginEarnedAALoad();
	// Reloads must discard profile entries for ranks no longer accepted below.
	memset(c->GetPP().aa_array, 0, sizeof(c->GetPP().aa_array));

	uint32 slot_id = 0;

	for (auto row : rows) {
		const uint32 aa_id    = Strings::ToUnsignedInt(row[0]);
		const uint32 aa_value = Strings::ToUnsignedInt(row[1]);
		const uint32 charges  = Strings::ToUnsignedInt(row[2]);

		auto ability = zone->GetAlternateAdvancementAbilityByRank(aa_id);
		auto rank = ability ? ability->GetRankByPointsSpent(aa_value) : nullptr;
		if (!ability || ability->first_rank_id != aa_id || !rank || rank->current_value != aa_value) {
			c->InvalidateEarnedAAState();
			continue;
		}

		c->RecordEarnedAA(aa_id, aa_value, charges);
		const auto active_count = std::min(aa_value, static_cast<uint32>(ability->GetMaxLevel(c)));
		if (!active_count) {
			continue;
		}
		if (slot_id >= MAX_PP_AA_ARRAY) {
			c->InvalidateEarnedAAState();
			return false;
		}
		if (c->SetAA(aa_id, active_count, charges)) {
			c->GetPP().aa_array[slot_id].AA      = aa_id;
			c->GetPP().aa_array[slot_id].value   = active_count;
			c->GetPP().aa_array[slot_id].charges = charges;

			slot_id++;
		} else {
			c->InvalidateEarnedAAState();
		}
	}

	return c->HasValidEarnedAAState();
}

AA::Ability *Zone::GetAlternateAdvancementAbility(int id) {
	auto iter = aa_abilities.find(id);
	if(iter != aa_abilities.end()) {
		return iter->second.get();
	}

	return nullptr;
}

AA::Ability *Zone::GetAlternateAdvancementAbilityByRank(int rank_id) {
	AA::Rank *rank = GetAlternateAdvancementRank(rank_id);

	if(!rank)
		return nullptr;

	return rank->base_ability;
}

AA::Rank *Zone::GetAlternateAdvancementRank(int rank_id) {
	auto iter = aa_ranks.find(rank_id);
	if(iter != aa_ranks.end()) {
		return iter->second.get();
	}

	return nullptr;
}

std::pair<AA::Ability*, AA::Rank*> Zone::GetAlternateAdvancementAbilityAndRank(int id, int points_spent) {
	AA::Ability *ability = GetAlternateAdvancementAbility(id);

	if(!ability) {
		return std::make_pair(nullptr, nullptr);
	}

	AA::Rank *rank = ability->GetRankByPointsSpent(points_spent);
	if(!rank) {
		return std::make_pair(nullptr, nullptr);
	}

	return std::make_pair(ability, rank);
}

uint32 Mob::GetAA(uint32 rank_id, uint32 *charges) const {
	if(zone) {
		AA::Ability *ability = zone->GetAlternateAdvancementAbilityByRank(rank_id);
		if(!ability)
			return 0;

		auto iter = aa_ranks.find(ability->id);
		if(iter != aa_ranks.end()) {
			if(charges) {
				*charges = iter->second.second;
			}
			return iter->second.first;
		}
	}
	return 0;
}

uint32 Mob::GetAAByAAID(uint32 aa_id, uint32 *charges) const {
	if(zone) {
		AA::Ability *ability = zone->GetAlternateAdvancementAbility(aa_id);

		if(!ability)
			return 0;

		auto iter = aa_ranks.find(ability->id);
		if(iter != aa_ranks.end()) {
			if(charges) {
				*charges = iter->second.second;
			}
			return iter->second.first;
		}
	}

	return 0;
}

bool Mob::SetAA(uint32 rank_id, uint32 new_value, uint32 charges)
{
	if (zone) {
		auto a = zone->GetAlternateAdvancementAbilityByRank(rank_id);

		if (!a) {
			return false;
		}

		if(new_value > a->GetMaxLevel(this)) {
			return false;
		}

		aa_ranks[a->id] = std::make_pair(new_value, charges);
	}

	return true;
}


bool Mob::CanUseAlternateAdvancementRank(AA::Rank *rank)
{
	if (!rank) {
		return false;
	}

	const auto a = rank->base_ability;

	if (!a) {
		return false;
	}

	if (IsClient()) {
		const auto required = NightcapAA::RequiredLevel(rank->id, a->id, rank->current_value, rank->expansion);
		if (!required) { return false; }
	}

	uint32 class_mask = IsClient() ? CastToClient()->GetClassMask() : (1 << GetClass());
	if (!(a->classes & class_mask)) {
		return false;
	}

	// Passive and Active Shroud AAs, skip for now
	if (
		a->category == AACategory::ShroudPassive ||
		a->category == AACategory::ShroudActive
	) {
		return false;
	}

	//the one titanium hack i will allow
	//just to make sure we dont crash the client with newer aas
	//we'll exclude any expendable ones
	if (IsClient() && CastToClient()->ClientVersionBit() & EQ::versions::maskTitaniumAndEarlier) {
		if (a->charges > 0) {
			return false;
		}
	}

	const int  expansion        = RuleI(Expansion, CurrentExpansion);
	const bool use_expansion_aa = RuleB(Expansion, UseCurrentExpansionAAOnly);
	if (use_expansion_aa && expansion >= 0) {
		if (rank->expansion > expansion) {
			return false;
		}
	}


	if (IsClient()) {
		if (rank->expansion) {
			if (rank->expansion < 0 || rank->expansion > 32) { return false; }
			const uint32 required_bit = uint32(1) << (rank->expansion - 1);
			auto *client = CastToClient();
			if (!(client->GetPP().expansions & required_bit)) {
				// The compiled policy above explicitly admits a small later-AA pool.
				// RoF2's native mask ends at19; do not mistake that client ceiling
				// for a restriction on an otherwise fully entitled curated build.
				// Deliberate profile/server/current-era restrictions still apply.
				const auto native_mask = EQ::expansions::ConvertClientVersionToExpansionsMask(client->ClientVersion());
				if (client->ClientVersion() != EQ::versions::ClientVersion::RoF2 ||
					!RuleB(World, UseClientBasedExpansionSettings) || !native_mask ||
					required_bit <= native_mask ||
					(client->GetPP().expansions & native_mask) != native_mask) {
					return false;
				}
			}
		}
	} else if (IsBot()) {
		if (rank->expansion && !(CastToBot()->GetExpansionBitmask() & (1 << (rank->expansion - 1)))) {
			return false;
		}
	} else {
		if (rank->expansion && !(RuleI(World, ExpansionSettings) & (1 << (rank->expansion - 1)))) {
			return false;
		}
	}

	auto race = GetPlayerRaceValue(GetBaseRace());

	race = race > RaceIndex::Drakkin ? Race::Human : race;

	if (!(a->races & (1 << (race - 1)))) {
		return false;
	}

	const auto deity = GetDeityBit();
	if (!(a->deities & deity)) {
		return false;
	}

	if (IsClient() && CastToClient()->Admin() < a->status) {
		return false;
	}

	if (GetBaseRace() == Race::Drakkin) {
		if (!(a->drakkin_heritage & (1 << GetDrakkinHeritage()))) {
			return false;
		}
	}

	return true;
}

bool Mob::CanPurchaseAlternateAdvancementRank(AA::Rank *rank, bool check_price, bool check_grant)
{
	auto a = rank->base_ability;

	if (!a) {
		return false;
	}

	if (!CanUseAlternateAdvancementRank(rank)) {
		return false;
	}

	if (IsClient() && (!CastToClient()->HasValidEarnedAAState() || CastToClient()->HasAlreadyPurchasedRank(rank))) {
		return false;
	}

	// You cannot purchase grant only AAs they can only be assigned
	if (check_grant && a->grant_only) {
		return false;
	}

	if (!IsClient() && rank->level_req > GetLevel()) {
		return false;
	}

	uint32       current_charges = 0;
	const uint32 points          = GetAA(rank->id, &current_charges);

	//check that we are on previous rank already (if exists)
	//grant ignores the req to own the previous rank.
	if (check_grant && rank->prev) {
		if (points != rank->prev->current_value) {
			return false;
		}
	}

	//check that we aren't already on this rank or one ahead of us
	if (points >= rank->current_value) {
		return false;
	}

	//if expendable only let us purchase if we have no charges already
	//not quite sure on how this functions client side atm
	//I intend to look into it later to make sure the behavior is right
	if (a->charges > 0 && current_charges > 0) {
		return false;
	}

	//check prereqs
	for (auto &prereq: rank->prereqs) {
		AA::Ability *prereq_ability = zone->GetAlternateAdvancementAbility(prereq.first);

		if (!prereq_ability || GetAA(prereq_ability->first_rank_id) < prereq.second) {
			return false;
		}
	}

	//check price, if client
	if (check_price && IsClient()) {
		if (rank->cost > CastToClient()->GetAAPoints()) {
			return false;
		}
	}

	return true;
}

void Zone::LoadAlternateAdvancement() {
	if (!content_db.LoadAlternateAdvancementAbilities(aa_abilities, aa_ranks)) {
		aa_abilities.clear();
		aa_ranks.clear();
		LogInfo("Failed to load Alternate Advancement Data");
		return;
	}

	for(const auto &ability : aa_abilities) {
		ability.second->first = GetAlternateAdvancementRank(ability.second->first_rank_id);

		//process these ranks
		AA::Rank *current = ability.second->first;
		int i = 1;
		int prev_id = -1;
		while(current) {
			current->prev_id = prev_id;
			current->prev = GetAlternateAdvancementRank(current->prev_id);
			current->next = GetAlternateAdvancementRank(current->next_id);
			current->base_ability = ability.second.get();
			current->current_value = i;
			current->recast_time = NightcapPetScaling::AAReuse(ability.first, i, current->recast_time);

			if(current->prev) {
				current->total_cost = current->cost + current->prev->total_cost;

				//check prereqs here
				for(auto &prev_prereq : current->prev->prereqs) {
					//if prev has an aa we dont have set
					//	then set it here too
					//if prev has an aa we have
					//	then set to whichever is highest

					auto iter = current->prereqs.find(prev_prereq.first);
					if(iter == current->prereqs.end()) {
						//not found
						current->prereqs[prev_prereq.first] = prev_prereq.second;
					} else {
						//they already have it too!
						auto points = std::max(iter->second, prev_prereq.second);
						current->prereqs[iter->first] = points;
					}
				}
			}
			else {
				current->prev_id = -1;
				current->total_cost = current->cost;
			}

			if(!current->next) {
				current->next_id = -1;
			}

			i++;
			prev_id = current->id;
			current = current->next;
		}
	}
}

bool ZoneDatabase::LoadAlternateAdvancementAbilities(
	std::unordered_map<int, std::unique_ptr<AA::Ability>> &abilities,
	std::unordered_map<int, std::unique_ptr<AA::Rank>> &ranks
)
{
	abilities.clear();

	const auto& aa_abilities = AaAbilityRepository::GetWhere(*this, "`enabled` = 1");

	if (aa_abilities.empty()) {
		LogError("Failed to load Alternate Advancement Abilities.");
		return false;
	}

	for (const auto& e : aa_abilities) {
		auto a = new AA::Ability;

		a->id                 = e.id;
		a->name               = e.name;
		a->category           = e.category;
		a->classes            = e.classes << 1; // EQ client has classes left shifted by one bit
		a->races              = e.races;
		a->deities            = e.deities;
		a->drakkin_heritage   = e.drakkin_heritage;
		a->status             = e.status;
		a->type               = e.type;
		a->charges            = e.charges;
		a->grant_only         = e.grant_only;
		a->reset_on_death     = e.reset_on_death;
		a->auto_grant_enabled = e.auto_grant_enabled;
		a->first_rank_id      = e.first_rank_id;
		a->first              = nullptr;

		abilities[a->id] = std::unique_ptr<AA::Ability>(a);
	}

	LogInfo(
		"Loaded [{}] Alternate Advancement Abilit{}.",
		Strings::Commify(abilities.size()),
		abilities.size() != 1 ? "ies" : "y"
	);

	ranks.clear();

	const auto& aa_ranks = AaRanksRepository::All(*this);

	if (aa_ranks.empty()) {
		LogError("Failed to load Alternate Advancement Ability Ranks.");
		return false;
	}

	for (const auto &e : aa_ranks) {
		auto r = new AA::Rank;

		r->id               = e.id;
		r->upper_hotkey_sid = e.upper_hotkey_sid;
		r->lower_hotkey_sid = e.lower_hotkey_sid;
		r->title_sid        = e.title_sid;
		r->desc_sid         = e.desc_sid;
		r->cost             = e.cost;
		r->level_req        = e.level_req;
		r->spell            = e.spell;
		r->spell_type       = e.spell_type;
		r->recast_time      = e.recast_time;
		r->next_id          = e.next_id;
		r->expansion        = e.expansion;
		r->base_ability     = nullptr;
		r->total_cost       = 0;
		r->prev_id          = -1;
		r->next             = nullptr;
		r->prev             = nullptr;

		ranks[r->id] = std::unique_ptr<AA::Rank>(r);
	}

	LogInfo(
		"Loaded [{}] Alternate Advancement Ability Rank{}.",
		Strings::Commify(ranks.size()),
		ranks.size() != 1 ? "s" : ""
	);

	const auto& aa_rank_effects = AaRankEffectsRepository::All(*this);

	if (aa_rank_effects.empty()) {
		LogError("Failed to load Alternate Advancement Ability Rank Effects.");
		return false;
	}

	for (const auto &e : aa_rank_effects) {
		AA::RankEffect f;

		f.slot        = e.slot;
		f.effect_id   = e.effect_id;
		f.base_value  = e.base1;
		f.limit_value = e.base2;

		if (f.slot < 1) {
			continue;
		}

		if (ranks.count(e.rank_id) > 0) {
			AA::Rank* r = ranks[e.rank_id].get();
			r->effects.push_back(f);
		}
	}

	LogInfo(
		"Loaded [{}] Alternate Advancement Ability Rank Effect{}.",
		Strings::Commify(aa_rank_effects.size()),
		aa_rank_effects.size() != 1 ? "s" : ""
	);

	const auto& aa_rank_prereqs = AaRankPrereqsRepository::All(*this);

	if (aa_rank_prereqs.empty()) {
		LogError("Failed to load Alternate Advancement Ability Rank Prerequisites.");
		return false;
	}

	for (const auto& e : aa_rank_prereqs) {
		if (e.aa_id <= 0 || e.points <= 0 || NightcapAA::WaivesPrerequisite(e.rank_id, e.aa_id)) {
			continue;
		}

		if (ranks.count(e.rank_id) > 0) {
			AA::Rank* rank = ranks[e.rank_id].get();
			rank->prereqs[e.aa_id] = e.points;
		}
	}

	LogInfo(
		"Loaded [{}] Alternate Advancement Ability Rank Prerequisite{}.",
		Strings::Commify(aa_rank_prereqs.size()),
		aa_rank_prereqs.size() != 1 ? "s" : ""
	);

	return true;
}

bool Mob::CheckAATimer(int timer)
{
	if (timer >= aaTimerMax)
		return false;
	if (aa_timers[timer].Enabled()) {
		if (aa_timers[timer].Check(false)) {
			aa_timers[timer].Disable();
			return false;
		} else {
			return true;
		}
	}
	return false;
}

void Client::TogglePassiveAlternativeAdvancement(const AA::Rank &rank, uint32 ability_id)
{
	/*
		Certain AA, like Weapon Stance line use a special toggle Hotkey to enable or disable the AA's passive abilities.
		This is occurs by doing the following. Each 'rank' of Weapon Stance is actually 2 actual ranks.
		First rank is always the Disabled version which cost X amount of AA. Second rank is the Enabled version which cost 0 AA.
		When you buy the first rank, you make a hotkey that on live say 'Weapon Stance Disabled', if you clik that it then BUYS the
		next rank of AA (cost 0) which switches the hotkey to 'Enabled Weapon Stance' and you are given the passive buff effects.
		If you click the Enabled hotkey, it causes you to lose an AA rank and once again be disabled. Thus, you are switching between
		two AA ranks. Thefore when creating an AA using this ability, you need generate both ranks. Follow the same pattern for additional ranks.

		IMPORTANT! The toggle system can be used to Enable or Disable ANY passive AA. You just need to follow the instructions on how to create it.
		Example: Enable or Disable a buff that gives a large hate modifier. Play may Enable when tanking and Disable when DPS ect.

		Note: On live the Enabled rank is shown having a Charge of 1, while Disabled rank has no charges. Our current code doesn't support that. Do not use charges.
		Note: Live uses a spell 'Disable Ability' ID 46164 to trigger a script to do the AA rank changes. At present time it is not coded to require that, any spell id works.
		Note: Discovered a bug on ROF2, where when you buy first rank of an AA with a hotkey, it will always display the title of the second rank in the database. Be aware. No easy fix.

		Dev Note(Kayen 8/1/21): The system as set up is very similar to live, with exception that live gives the Enabled rank 1 Charge. The code here emulates what happens when a
		charge would be expended.

		Instructions for how to make the AA - assuming a basic level of knowledge of how AA's work.
		- aa_abilities table : Create new ability with a hotkey, type 3, zero charges
		- aa_ranks table :  [Disabled rank] First rank, should have a cost > 0 (this is what you buy), Set hotkeys, MUST SET A SPELL CONTAINING EFFECT SpellEffect::Buy_AA_Rank(SPA 472), set a short recast timer.
							[Enabled rank] Second rank, should have a cost = 0, Set hotkeys, Set any valid spell ID you want (it has to exist but does nothing), set a short recast timer.
							*Recommend if doing custom, just make the hotkey titled 'Toggle <Ability Name>' and use for both.

		- aa_rank_effects table : [Disabled rank] No data needed in the aa_ranks_effect table
								  [Enabled rank]  Second rank set effect_id = 457 (weapon stance), slot 1,2,3, base1= spell triggers, base= weapon type (0=2H,1=SH,2=DW), for slot 1,2,3

			Example SQL			-Disabled
								DO NOT ADD any data to the aa_rank_effects for this rank_id

								-Enabled
								INSERT INTO aa_rank_effects (rank_id, slot, effect_id, base1, base2) VALUES (20003, 1, 476, 145,0);
								INSERT INTO aa_rank_effects (rank_id, slot, effect_id, base1, base2) VALUES (20003, 2, 476, 174,1);
								INSERT INTO aa_rank_effects (rank_id, slot, effect_id, base1, base2) VALUES (20003, 3, 476, 172,2);

		Warning: If you want to design an AA that only uses one weapon type to trigger, like will only apply buff if Shield. Do not include data for other types. Never have a base value=0
		in the Enabled rank.

	*/

	bool enable_next_rank = IsEffectInSpell(rank.spell, SpellEffect::Buy_AA_Rank);

	if (enable_next_rank) {

		//Enable
		TogglePurchaseAlternativeAdvancementRank(rank.next_id);
		Message(Chat::Spells, "You enable an ability."); //Message live gives you. Should come from spell.

		AA::Rank *rank_next = zone->GetAlternateAdvancementRank(rank.next_id);

		//Add checks for any special cases for toggle.
		if (rank_next && IsEffectinAlternateAdvancementRankEffects(*rank_next, SpellEffect::Weapon_Stance)) {
			weaponstance.aabonus_enabled = true;
			ApplyWeaponsStance();
		}
		return;
	}
	else {

		//Disable
		ResetAlternateAdvancementRank(ability_id);
		TogglePurchaseAlternativeAdvancementRank(rank.prev_id);
		Message(Chat::Spells, "You disable an ability."); //Message live gives you. Should come from spell.

		//Add checks for any special cases for toggle.
		if (IsEffectinAlternateAdvancementRankEffects(rank, SpellEffect::Weapon_Stance)) {
			weaponstance.aabonus_enabled = false;
			BuffFadeBySpellID(weaponstance.aabonus_buff_spell_id);
		}
		return;
	}
}

bool Client::UseTogglePassiveHotkey(const AA::Rank &rank) {

	/*
		Disabled rank needs a rank spell containing the SpellEffect::Buy_AA_Rank effect to return true.
		Enabled rank checks to see if the prior rank contains a rank spell with SpellEffect::Buy_AA_Rank, if so true.

		Note: On live the enabled rank is Expendable with Charge 1.

		We have already confirmed the rank spell is valid before this function is called.
	*/


	if (IsEffectInSpell(rank.spell, SpellEffect::Buy_AA_Rank)) {//Checked when is Disabled.
		return true;
	}
	else if (rank.prev_id != -1) {//Check when effect is Enabled.
		AA::Rank *rank_prev = zone->GetAlternateAdvancementRank(rank.prev_id);

		if (rank_prev && IsEffectInSpell(rank_prev->spell, SpellEffect::Buy_AA_Rank)) {
			return true;
		}
	}
	return false;
}

bool Client::IsEffectinAlternateAdvancementRankEffects(const AA::Rank &rank, int effect_id) {

	for (const auto &e : rank.effects) {

		if (e.effect_id == effect_id) {
			return true;
		}
	}
	return false;
}

void Client::ResetAlternateAdvancementRank(uint32 aa_id) {
	auto ability = zone->GetAlternateAdvancementAbility(aa_id);
	if (ability && RemoveExpendedAA(ability->first_rank_id)) {
		CalcBonuses();
		SendAlternateAdvancementPoints();
	}
}

void Client::TogglePurchaseAlternativeAdvancementRank(int rank_id){

	/*
		Stripped down version of purchasing AA. Will give no messages.
		Used with toggle hotkey functions.
	*/

	AA::Rank *rank = zone->GetAlternateAdvancementRank(rank_id);
	if (!rank) {
		return;
	}

	if (!rank->base_ability) {
		return;
	}

	if (!CanPurchaseAlternateAdvancementRank(rank, false, false)) {
		return;
	}

	rank_id = rank->base_ability->first_rank_id;
	SetAA(rank_id, rank->current_value, 0);

	if (rank->next) {
		SendAlternateAdvancementRank(rank->base_ability->id, rank->next->current_value);
	}

	SaveAA();
	SendAlternateAdvancementPoints();
	SendAlternateAdvancementStats();
	CalcBonuses();
}

void Client::AutoGrantAAPoints() {
	int auto_grant_expansion = RuleI(Expansion, AutoGrantAAExpansion);

	if (auto_grant_expansion == -1) {
		return;
	}

	//iterate through every AA
	for (auto& iter : zone->aa_abilities) {
		auto ability = iter.second.get();

		if (ability->grant_only) {
			continue;
		}

		if (ability->charges > 0) {
			continue;
		}

		if (!ability->auto_grant_enabled) {
			continue;
		}

		auto p = 1;
		auto rank = ability->first;
		while (rank != nullptr) {
			if (CanUseAlternateAdvancementRank(rank)) {
				if (rank->expansion <= auto_grant_expansion && !HasAlreadyPurchasedRank(rank)) {
					if (!FinishAlternateAdvancementPurchase(rank, true, false)) {
						return;
					}

					if (rank->prev) {
						MessageString(
							Chat::Yellow,
							AA_IMPROVE,
							std::to_string(rank->title_sid).c_str(),
							std::to_string(rank->prev->current_value).c_str(),
							"0",
							std::to_string(AA_POINTS).c_str()
						);
					}
					else {
						MessageString(
							Chat::Yellow,
							AA_GAIN_ABILITY,
							std::to_string(rank->title_sid).c_str(),
							"0",
							std::to_string(AA_POINTS).c_str()
						);
					}
				}
			}
			else {
				break;
			}

			p++;
			rank = rank->next;
		}
	}

	SendClearLeadershipAA();
	SendClearPlayerAA();
	SendAlternateAdvancementTable();
	SendAlternateAdvancementPoints();
	SendAlternateAdvancementStats();
}

void Client::GrantAllAAPoints(uint8 unlock_level, bool skip_grant_only)
{
	//iterate through every AA
	for (auto& aa : zone->aa_abilities) {
		AA::Ability* ability = aa.second.get();

		if (ability->charges > 0) {
			continue;
		}

		if (ability->grant_only && skip_grant_only) {
			continue;
		}

		// An explicit GM content-level filter is separate from player access.

		AA::Rank* rank = ability->first;
		while (rank) {
			if (!CanUseAlternateAdvancementRank(rank)) {
				break;
			}

			if ((!unlock_level || rank->level_req <= unlock_level) && !HasAlreadyPurchasedRank(rank)) {
				if (!FinishAlternateAdvancementPurchase(rank, true, false)) {
					return;
				}
			}

			rank = rank->next;
		}
	}

	SendClearLeadershipAA();
	SendClearPlayerAA();
	SendAlternateAdvancementTable();
	SendAlternateAdvancementPoints();
	SendAlternateAdvancementStats();
}

bool Client::HasAlreadyPurchasedRank(AA::Rank* rank) {
	if (GetEarnedAACount(rank->base_ability->first_rank_id) >= rank->current_value) {
		return true;
	}
	const auto& aa = aa_ranks.find(rank->base_ability->id);
	if (aa == aa_ranks.end()) {
		return false;
	}

	const auto& ability_rank = zone->GetAlternateAdvancementAbilityAndRank(aa->first, aa->second.first);

	AA::Ability* ability = ability_rank.first;
	AA::Rank*    current = ability_rank.second;

	while (current) {
		if (current == rank) {
			return true;
		}

		current = current->prev;
	}

	return false;
}

void Client::ListPurchasedAAs(Client *to, std::string search_criteria)
{
	if (!to) {
		return;
	}

	std::map<std::string, uint8> client_aa_ranks;

	for (auto &aa : zone->aa_abilities) {
		AA::Ability *ability = aa.second.get();

		AA::Rank *rank = ability->first;
		while (rank) {
			if (!CanUseAlternateAdvancementRank(rank)) {
				break;
			}

			if (HasAlreadyPurchasedRank(rank)) {
				const std::string aa_name = zone->GetAAName(rank->id);
				if (
					search_criteria.empty() ||
					Strings::Contains(
						Strings::ToLower(aa_name),
						Strings::ToLower(search_criteria)
					)
				) {
					if (client_aa_ranks.find(aa_name) == client_aa_ranks.end()) {
						client_aa_ranks[aa_name] = 1;
					} else {
						client_aa_ranks[aa_name]++;
					}
				}
			}

			rank = rank->next;
		}
	}

	if (client_aa_ranks.empty()) {
		to->Message(
			Chat::White,
			fmt::format(
				"{} {} no purchased AAs{}.",
				to->GetTargetDescription(this, TargetDescriptionType::UCYou),
				this == to ? "have" : "has",
				(
					!search_criteria.empty() ?
					fmt::format(
						" matching '{}'",
						search_criteria
					) :
					""
				)
			).c_str()
		);
		return;
	}

	int aa_number = 1;

	for (const auto &aa : client_aa_ranks) {
		to->Message(
			Chat::White,
			fmt::format(
				"{}. {} (Rank {})",
				aa_number,
				aa.first,
				aa.second
			).c_str()
		);

		aa_number++;
	}

	to->Message(
		Chat::White,
		fmt::format(
			"{} {} {} purchased AA{}{}.",
			to->GetTargetDescription(this, TargetDescriptionType::UCYou),
			this == to ? "have" : "has",
			client_aa_ranks.size(),
			client_aa_ranks.size() > 1 ? "s" : "",
			(
				!search_criteria.empty() ?
				fmt::format(
					" matching '{}'",
					search_criteria
				) :
				""
			)
		).c_str()
	);
}
