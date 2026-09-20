#include "zone/client.h"
#include "zone/npc.h"
#include "zone/entity.h"
#include "common/pet_class_policy.h"

uint8 Client::GetPetSpellClass(uint16 spell_id) const
{
	if (m_restoring_pet_class) {
		return IsMulticlassMember(m_restoring_pet_class) && NightcapPetClasses::Eligible(
			spell_id, GetLevel(), m_restoring_pet_class, GetClass()) ? m_restoring_pet_class : 0;
	}
	return NightcapPetClasses::Resolve(spell_id, GetLevel(), {GetClass(), GetClass2(), GetClass3()});
}

bool Client::RegisterClassPet(uint8 class_id, NPC *pet)
{
	if (!pet || !class_id || GetClassPet(class_id) || !IsMulticlassMember(class_id) ||
		pet->GetOwnerID() != GetID() || pet->GetDepop() || pet->HasDied() ||
		pet->IsCharmed() || pet->GetSwarmInfo() || pet->GetPetType() == petTargetLock ||
		GetPetSpellClass(pet->GetPetSpellID()) != class_id) { return false; }
	m_class_pets[class_id] = pet->GetID();
	return true;
}

void Client::UnregisterClassPet(uint16 entity_id)
{
	for (auto it = m_class_pets.begin(); it != m_class_pets.end();) {
		if (it->second == entity_id) { it = m_class_pets.erase(it); }
		else { ++it; }
	}
	if (GetPetID() == entity_id) { SetPetID(0); }
}

std::vector<uint16> Client::GetExtraPetIds() const
{
	std::vector<uint16> ids;
	for (const auto &[class_id, id] : m_class_pets) {
		if (id != GetPetID()) { ids.push_back(id); }
	}
	return ids;
}

void Client::RefreshClassPets(bool force_window)
{
	if (m_suspended_pet_class && !IsMulticlassMember(m_suspended_pet_class)) {
		memset(&m_suspendedminion, 0, sizeof(m_suspendedminion));
		m_suspended_pet_class = 0;
	}
	for (auto it = m_class_pets.begin(); it != m_class_pets.end();) {
		auto mob = entity_list.GetMob(it->second);
		const bool owned = mob && mob->IsNPC() && mob->GetOwnerID() == GetID();
		if (!owned || mob->CastToNPC()->GetDepop() || mob->HasDied() || mob->IsCharmed() ||
			!IsMulticlassMember(it->first)) {
			// A committed class release removes its pet, never another owner's NPC.
			if (owned && !IsMulticlassMember(it->first) && !mob->IsCharmed()) { mob->Depop(false); }
			if (GetPetID() == it->second) { SetPetID(0); }
			it = m_class_pets.erase(it);
		} else { ++it; }
	}
	auto current = entity_list.GetMob(GetPetID());
	if (!current || !current->IsNPC() || current->GetOwnerID() != GetID() ||
		current->CastToNPC()->GetDepop() || current->HasDied()) { SetPetID(0); }
	if (!GetPetID() || (current && current->GetPetType() == petFamiliar)) {
		for (const auto class_id : GetMulticlassList()) {
			if (auto id = GetClassPet(class_id)) {
				auto candidate = entity_list.GetMob(id);
				if (candidate && candidate->GetPetType() != petFamiliar) { SetPetID(id); break; }
				if (!GetPetID()) { SetPetID(id); }
			}
		}
	}
	if (force_window || m_pet_window_id != GetPetID()) { SyncPetWindow(); }
}

std::vector<NPC *> Client::GetCommandPets()
{
	RefreshClassPets();
	std::vector<NPC *> pets;
	if (auto pet = GetPet()) {
		if (pet->IsNPC()) { pets.push_back(pet->CastToNPC()); }
	}
	for (const auto id : GetExtraPetIds()) {
		auto mob = entity_list.GetMob(id);
		if (mob && mob->IsNPC() && !mob->CastToNPC()->GetDepop() && !mob->HasDied() &&
			mob->GetOwnerID() == GetID()) { pets.push_back(mob->CastToNPC()); }
	}
	return pets;
}

void Client::SyncPetWindow()
{
	const auto old_id = m_pet_window_id;
	m_pet_window_id = GetPetID();
	EQApplicationPacket anchor(OP_Charm, sizeof(Charm_Struct));
	auto body = reinterpret_cast<Charm_Struct *>(anchor.pBuffer);
	body->owner_id = GetID();
	body->pet_id = m_pet_window_id ? m_pet_window_id : old_id;
	body->command = m_pet_window_id ? 1 : 0;
	QueuePacket(&anchor);
	auto pet = GetPet();
	if (!pet || !pet->IsNPC()) { return; }
	UpdateXTargetType(MyPetTarget, pet->GetTarget());
	pet->SendPetBuffsToClient();
	if (ClientVersionBit() & EQ::versions::maskUFAndLater) {
		EQApplicationPacket target(OP_PetHoTT, sizeof(ClientTarget_Struct));
		reinterpret_cast<ClientTarget_Struct *>(target.pBuffer)->new_target = pet->GetTarget() ? pet->GetTarget()->GetID() : 0;
		QueuePacket(&target);
		SetPetCommandState(PetButton::Sit, pet->GetPetOrder() == SPO_Sit);
		SetPetCommandState(PetButton::Stop, pet->IsPetStop());
		SetPetCommandState(PetButton::Regroup, pet->IsPetRegroup());
		SetPetCommandState(PetButton::Follow, pet->GetPetOrder() == SPO_Follow);
		SetPetCommandState(PetButton::Guard, pet->GetPetOrder() == SPO_Guard);
		SetPetCommandState(PetButton::Hold, pet->IsHeld());
		SetPetCommandState(PetButton::GreaterHold, pet->IsGHeld());
		SetPetCommandState(PetButton::Focus, pet->IsFocused());
		SetPetCommandState(PetButton::SpellHold, pet->IsNoCast());
	}
}

void Client::CaptureClassPets()
{
	memset(&m_petinfo, 0, sizeof(m_petinfo));
	for (auto &info : m_class_pet_info) { memset(&info, 0, sizeof(info)); }
	if (dead) { return; }
	RefreshClassPets();
	for (const auto &[class_id, id] : m_class_pets) {
		auto pet = GetArmorPet(class_id);
		if (!pet || !IsValidSpell(pet->GetPetSpellID())) { continue; }
		auto &info = m_class_pet_info[class_id - 1];
		info.SpellID = pet->GetPetSpellID();
		info.HP = pet->GetHP();
		info.Mana = pet->GetMana();
		pet->GetPetState(info.Buffs, info.Items, info.Name);
		info.petpower = pet->GetPetPower();
		info.size = pet->GetSize();
		info.taunting = pet->IsTaunting();
	}
}

void Client::RestoreClassPets()
{
	if (!m_pet_state_valid) { return; }
	std::vector<std::pair<NPC *, PetInfo *>> restored;
	// Slot 0 is read only for migration from the old single-pet save format.
	for (int type = 0; type <= 17; ++type) {
		if (type == PetInfoType::Suspended) { continue; }
		auto info = GetPetInfo(type);
		if (!info || !IsValidSpell(info->SpellID)) { continue; }
		m_restoring_pet_class = type >= 2 ? type - 1 : 0;
		const auto class_id = GetPetSpellClass(info->SpellID);
		if (!class_id || GetClassPet(class_id)) { m_restoring_pet_class = 0; continue; }
		MakePoweredPet(info->SpellID, spells[info->SpellID].teleport_zone, info->petpower, info->Name, info->size);
		m_restoring_pet_class = 0;
		auto pet = GetArmorPet(class_id);
		if (!pet) { InvalidatePetState(); return; }
		pet->SetPetState(info->Buffs, info->Items);
		pet->CalcBonuses();
		restored.emplace_back(pet, info);
		if ((m_ClientVersionBit & EQ::versions::maskUFAndLater) && !ingame) { pet->SetTaunting(info->taunting); }
	}
	ApplyPetArmor();
	for (const auto &[pet, info] : restored) {
		pet->SetHP(info->HP);
		pet->SetMana(info->Mana);
	}
	RefreshClassPets(true);
}
