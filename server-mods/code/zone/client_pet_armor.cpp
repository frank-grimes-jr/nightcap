#include "zone/client.h"
#include "zone/npc.h"
#include "zone/entity.h"
#include <iterator>

namespace {
std::string ArmorText(const char *text)
{
	std::string hex;
	for (size_t i = 0; text && text[i] && i < 63; ++i) {
		const auto c = static_cast<unsigned char>(text[i]);
		hex += "0123456789abcdef"[c >> 4]; hex += "0123456789abcdef"[c & 15];
	}
	return hex;
}
}

bool Client::LoadPetArmor()
{
	if (m_pet_armor_loaded) { return true; }
	if (m_pet_armor_unavailable || !NightcapPetArmor::Load(CharacterID(), m_pet_armor)) {
		m_pet_armor_unavailable = true;
		return false;
	}
	m_pet_armor_loaded = true;
	return true;
}

NPC *Client::GetArmorPet(uint8 pet_class)
{
	if (pet_class < 1 || pet_class > 16 ||
		(pet_class != GetClass() && pet_class != GetClass2() && pet_class != GetClass3())) { return nullptr; }
	const auto id = GetClassPet(pet_class);
	const auto mob = entity_list.GetMob(id);
	if (!mob || !mob->IsNPC() || mob->GetOwnerID() != GetID() || !mob->IsPet() || mob->IsCharmed() ||
		mob->CastToNPC()->GetDepop() || mob->HasDied() || mob->CastToNPC()->GetSwarmInfo() || mob->GetPetType() == PetType::TargetLock) { return nullptr; }
	return mob->CastToNPC();
}

void Client::ApplyPetArmor()
{
	SendPetManagement();
	if (!LoadPetArmor()) { return; }
	std::map<uint8, uint16> roster;
	for (uint8 pet_class = 1; pet_class <= 16; ++pet_class) {
		auto pet = GetArmorPet(pet_class);
		if (!pet) { continue; }
		roster[pet_class] = pet->GetID();
		const NightcapPetArmor::Equipment empty{};
		const auto found = m_pet_armor.find(pet_class);
		const auto &items = found == m_pet_armor.end() ? empty : found->second;
		for (uint8 i = 0; i < NightcapPetArmor::Slots.size(); ++i) {
			// Reserve a conflicting native hand without deleting its temporary item.
			// The setter only suppresses a primary hand if it is a two-handed weapon.
			const bool reserve = (i == 8 && items[9].instance) ||
				(i == 9 && items[8].instance && items[8].instance->GetItem()->IsType2HWeapon());
			pet->SetNightcapPetArmor(i, items[i].instance, reserve);
		}
	}
	if (roster != m_pet_armor_roster) {
		m_pet_armor_roster = std::move(roster);
		if (m_pet_armor_ui_enabled) { SendPetArmor(); }
	}
}

bool Client::PetArmorLoreConflict(const EQ::ItemData *item)
{
	if (!item || !item->LoreFlag || !item->LoreGroup) { return false; }
	if (!LoadPetArmor()) { return true; } // cannot prove absence of an owned lore item
	auto conflict = [&](const EQ::ItemData *owned) {
		return owned && (item->LoreGroup == -1 ? item->ID == owned->ID : item->LoreGroup == owned->LoreGroup);
	};
	for (const auto &[pet_class, equipment] : m_pet_armor) {
		for (const auto &entry : equipment) {
			if (!entry.instance) { continue; }
			if (conflict(entry.instance->GetItem())) { return true; }
			for (int i = 0; i < EQ::invaug::SOCKET_COUNT; ++i) {
				const auto aug = entry.instance->GetAugment(i);
				if (aug && conflict(aug->GetItem())) { return true; }
			}
		}
	}
	return false;
}

void Client::SendPetArmor()
{
	if (!zone || !LoadPetArmor()) {
		Message(Chat::Red, "Pet armor storage is unavailable. Your items have not been moved.");
		return;
	}
	if (!m_pet_armor_nonce) { m_pet_armor_nonce = zone->random.Int(1, INT32_MAX); }
	if (++m_pet_armor_nonce == 0) { ++m_pet_armor_nonce; }
	Message(Chat::White, "[NCPA2]B|%u|%u|%u|%u|%u|%s", m_pet_armor_nonce,
		CharacterID(), zone->GetZoneID(), zone->GetInstanceID(), GetID(), ArmorText(GetCleanName()).c_str());
	for (uint8 pet_class = 1; pet_class <= 16; ++pet_class) {
		const auto pet = GetArmorPet(pet_class);
		const auto stored = m_pet_armor.find(pet_class);
		bool has_items = stored != m_pet_armor.end() && std::any_of(stored->second.begin(), stored->second.end(),
			[](const auto &entry) { return entry.instance != nullptr; });
		if (!pet && !has_items) { continue; }
		Message(Chat::White, "[NCPA2]P|%u|%u|%u|%s", m_pet_armor_nonce, pet_class,
			pet ? pet->GetID() : 0, ArmorText(pet ? pet->GetCleanName() : "Stored armor").c_str());
		for (uint8 i = 0; i < NightcapPetArmor::Slots.size(); ++i) {
			const auto inst = stored == m_pet_armor.end() ? nullptr : stored->second[i].instance;
			Message(Chat::White, "[NCPA2]I|%u|%u|%u|%u|%s", m_pet_armor_nonce, pet_class, i,
				inst ? inst->GetID() : 0, ArmorText(inst ? inst->GetItem()->Name : "Empty").c_str());
		}
	}
	Message(Chat::White, "[NCPA2]E|%u", m_pet_armor_nonce);
}

void Client::SendPetManagement()
{
	if (!m_pet_management_enabled || !zone) { return; }
	GetSelectedCommandPets(); // discard a selection whose exact spawn no longer exists
	const auto pets = GetCommandPets();
	if (!m_pet_management_token) { m_pet_management_token = zone->random.Int(1, INT32_MAX); }
	if (++m_pet_management_generation == 0) { ++m_pet_management_generation; }
	std::string rows;
	unsigned count = 0;
	std::map<uint8, NPC *> ordered;
	for (auto pet : pets) {
		uint8 pet_class = GetClass();
		for (const auto &[class_id, id] : m_class_pets) {
			if (id == pet->GetID()) { pet_class = class_id; break; }
		}
		ordered[pet_class] = pet;
	}
	for (const auto &[pet_class, pet] : ordered) {
		if (count == 3) { break; }
		rows += fmt::format("|{}|{}|{}|{}", pet_class, pet->GetID(),
			std::clamp(static_cast<int>(pet->GetHPRatio()), 0, 100), ArmorText(pet->GetCleanName()));
		++count;
	}
	Message(Chat::White, "[NCPM1]|%u|%u|%u|%u|%u|%u|%s|%u|%u%s", m_pet_management_token,
		m_pet_management_generation, CharacterID(), zone->GetZoneID(), zone->GetInstanceID(),
		GetID(), ArmorText(GetCleanName()).c_str(), m_selected_command_pet, count, rows.c_str());
}

void Client::HandlePetArmor(const Seperator *sep)
{
	if (!sep || !zone || !Connected()) { return; }
	if (sep->argnum == 1 && !strcmp(sep->arg[1], "manage")) {
		if (m_pet_management_enabled && !m_pet_armor_view_timer.Check()) { return; }
		m_pet_armor_view_timer.Start(3000);
		m_pet_management_enabled = true;
		SendPetManagement();
		return;
	}
	if (sep->argnum == 3 && (!strcmp(sep->arg[1], "select") || !strcmp(sep->arg[1], "order"))) {
		if (!m_pet_management_enabled) { return; }
		RefreshClassPets(); // invalidate stale scope before accepting its token
		for (int i = 2; i <= 3; ++i) {
			const std::string value = sep->arg[i];
			if (value.empty() || value.size() > 10 || value.find_first_not_of("0123456789") != std::string::npos ||
				strtoull(value.c_str(), nullptr, 10) > UINT32_MAX) { return; }
		}
		const uint32 id = Strings::ToUnsignedInt(sep->arg[2]);
		const uint32 token = Strings::ToUnsignedInt(sep->arg[3]);
		if (id > UINT16_MAX || !token || token != m_pet_management_token) { return; }
		if (!strcmp(sep->arg[1], "order")) {
			if (id >= PET_MAXCOMMANDS) { return; }
			EQApplicationPacket packet(OP_PetCommands, sizeof(PetCommand_Struct));
			auto body = reinterpret_cast<PetCommand_Struct *>(packet.pBuffer);
			body->command = id;
			body->target = GetTarget() ? GetTarget()->GetID() : 0;
			Handle_OP_PetCommands(&packet);
			SendPetManagement();
			return;
		}
		if (!SelectCommandPet(static_cast<uint16>(id))) { SendPetManagement(); }
		return;
	}
	if (sep->argnum == 1 && !strcmp(sep->arg[1], "view")) {
		if (m_pet_armor_ui_enabled && !m_pet_armor_view_timer.Check()) { return; }
		m_pet_armor_view_timer.Start(3000);
		m_pet_armor_ui_enabled = true;
		SendPetArmor();
		return;
	}
	if (!m_pet_armor_ui_enabled || sep->argnum != 4) { return; }
	const std::string action = sep->arg[1];
	if (action != "equip" && action != "remove" && action != "inspect") { return; }
	for (int i = 2; i <= 4; ++i) {
		const std::string value = sep->arg[i];
		if (value.empty() || value.size() > 10 || value.find_first_not_of("0123456789") != std::string::npos ||
			strtoull(value.c_str(), nullptr, 10) > UINT32_MAX) { return; }
	}
	const uint32 pet_class = Strings::ToUnsignedInt(sep->arg[2]);
	const uint32 index = Strings::ToUnsignedInt(sep->arg[3]);
	const uint32 nonce = Strings::ToUnsignedInt(sep->arg[4]);
	if (pet_class < 1 || pet_class > 16 || index >= NightcapPetArmor::Slots.size() || !LoadPetArmor()) { return; }
	if (!nonce || nonce != m_pet_armor_nonce) {
		Message(Chat::Yellow, "Pet armor changed. Check the refreshed tab and try again.");
		SendPetArmor();
		return;
	}
	const auto pet = GetArmorPet(pet_class);
	auto &stored = m_pet_armor[pet_class][index];
	if (action == "inspect") {
		if (stored.instance) {
			SendItemPacket(0, stored.instance.get(), ItemPacketViewLink);
		}
		return;
	}
	if (IsDead() || IsEngaged() || auto_attack || IsCasting() || IsStunned() || IsMezzed() || IsFeared() ||
		IsAIControlled() || (trade && trade->With()) || GetTradeskillObject() || (pet && pet->IsEngaged())) {
		Message(Chat::Red, "Finish combat, casting, or trading before changing pet armor.");
		return;
	}
	if (pet && glm::distance(glm::vec3(GetPosition()), glm::vec3(pet->GetPosition())) > 50.0f) {
		Message(Chat::Red, "Bring your pet closer before changing its armor.");
		return;
	}
	const bool equip = action == "equip";
	const auto cursor = m_inv.GetItem(EQ::invslot::slotCursor);
	const auto queue = std::distance(m_inv.cursor_cbegin(), m_inv.cursor_cend());
	if (equip && !NightcapPetArmor::CanEquip(m_pet_armor[pet_class], pet_class, index, cursor)) {
		Message(Chat::Red, "Choose a compatible empty location within this pet's %u-item limit. Two-handed weapons exclude the offhand.",
			NightcapPetArmor::Capacity(pet_class));
		return;
	}
	if (equip ? (!pet || stored.instance || queue != 1 || !NightcapPetArmor::Allowed(cursor, index)) :
		(!stored.instance || cursor || queue != 0)) {
		Message(Chat::Red, equip ? "Place one compatible armor item on your cursor and select an empty slot on an active pet." :
			"Empty your cursor before removing an equipped item.");
		return;
	}
	if (!equip) {
		if (CheckLoreConflict(stored.instance->GetItem(), false)) {
			Message(Chat::Red, "You already have a conflicting lore item in your inventory."); return;
		}
		for (int i = 0; i < EQ::invaug::SOCKET_COUNT; ++i) {
			const auto aug = stored.instance->GetAugment(i);
			if (aug && CheckLoreConflict(aug->GetItem(), false)) {
				Message(Chat::Red, "You already have a conflicting lore augment in your inventory."); return;
			}
		}
	}
	NightcapPetArmor::Item moved;
	if (!NightcapPetArmor::Transfer(CharacterID(), pet_class, index, equip, cursor, stored, moved)) {
		// A lost COMMIT acknowledgement must not be followed by a stale cursor save.
		m_pet_armor_transfer_valid = false;
		client_data_loaded = false;
		Message(Chat::Red, "The armor transfer could not be confirmed. Please reconnect to reload your items.");
		if (eqs) { eqs->Close(); }
		client_state = DISCONNECTED;
		return;
	}
	if (equip) {
		stored = std::move(moved);
		DeleteItemInInventory(EQ::invslot::slotCursor, 0, true, false);
	} else {
		stored = {};
		m_inv.PushCursor(*moved.instance);
		SendItemPacket(EQ::invslot::slotCursor, moved.instance.get(), ItemPacketLimbo);
	}
	ApplyPetArmor();
	SendPetArmor();
}

void NPC::SetNightcapPetArmor(uint8 index, const std::shared_ptr<EQ::ItemInstance> &inst, bool reserve_hand)
{
	if (index >= NightcapPetArmor::Slots.size()) { return; }
	const int16 slot = NightcapPetArmor::Slots[index];
	if (slot == EQ::invslot::slotPrimary && reserve_hand) {
		const auto original = m_nightcap_armor_active[index] ? m_nightcap_armor_base[index].get() : GetInv().GetItem(slot);
		reserve_hand = original && original->GetItem()->IsType2HWeapon();
	}
	const bool active = inst || reserve_hand;
	if (!active && !m_nightcap_armor_active[index]) { return; }
	if (!inst && reserve_hand && m_nightcap_armor_active[index] && !GetInv().GetItem(slot)) { return; }
	if (inst && m_nightcap_armor_active[index] && GetInv().GetItem(slot) &&
		GetInv().GetItem(slot)->GetSerialNumber() == inst->GetSerialNumber()) { return; }
	if (active && !m_nightcap_armor_active[index]) {
		const auto original = GetInv().GetItem(slot);
		m_nightcap_armor_base[index].reset(original ? original->Clone() : nullptr);
	}
	const auto replacement = inst ? inst : reserve_hand ? nullptr : m_nightcap_armor_base[index];
	if (replacement) { GetInv().PutItem(slot, *replacement); }
	else { GetInv().DeleteItem(slot); }
	equipment[slot] = replacement ? replacement->GetID() : 0;
	m_nightcap_armor_active[index] = active;
	if (!active) { m_nightcap_armor_base[index].reset(); }
	CalcBonuses();
	SetAttackTimer();
	const auto material = EQ::InventoryProfile::CalcMaterialFromSlot(slot);
	if (material != static_cast<uint8>(EQ::textures::materialInvalid)) { SendWearChange(material); }
	UpdateEquipmentLight();
	if (UpdateActiveLight()) { SendAppearancePacket(AppearanceType::Light, GetActiveLightType()); }
}

bool NPC::IsNightcapPetArmorSlot(int16 slot) const
{
	for (size_t i = 0; i < NightcapPetArmor::Slots.size(); ++i) {
		if (NightcapPetArmor::Slots[i] == slot && m_nightcap_armor_active[i]) { return true; }
	}
	return false;
}
