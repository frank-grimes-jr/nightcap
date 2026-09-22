#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

using uint8 = uint8_t;
using uint16 = uint16_t;
using uint32 = uint32_t;
constexpr int petFamiliar = 0;
constexpr int petOther = 2;
struct NPC;
struct Mob {
	uint16 id = 0, owner = 10;
	bool npc = true, depop = false, dead = false, charmed = false;
	int type = petOther;
	uint16 GetID() const { return id; }
	uint16 GetOwnerID() const { return owner; }
	bool IsNPC() const { return npc; }
	bool HasDied() const { return dead; }
	bool IsCharmed() const { return charmed; }
	int GetPetType() const { return type; }
	void Depop(bool) { depop = true; }
	NPC* CastToNPC() { return reinterpret_cast<NPC*>(this); }
};
struct NPC : Mob { bool GetDepop() const { return depop; } };
struct Entities {
	std::map<uint16, NPC*> mobs;
	Mob* GetMob(uint16 id) { auto it = mobs.find(id); return it == mobs.end() ? nullptr : it->second; }
} entity_list;

struct Timer { bool Check() const { return true; } void Start(unsigned) {} };
struct Zone {};
Zone test_zone;
Zone* zone = &test_zone;
struct Seperator {
	int argnum;
	const char* arg[5];
};
namespace Strings { uint32 ToUnsignedInt(const char* text) { return static_cast<uint32>(strtoull(text, nullptr, 10)); } }
constexpr int OP_PetCommands = 1;
constexpr unsigned PET_MAXCOMMANDS = 34;
struct PetCommand_Struct { uint32 command, target; };
struct EQApplicationPacket {
	alignas(4) unsigned char buffer[sizeof(PetCommand_Struct)]{};
	unsigned char* pBuffer = buffer;
	EQApplicationPacket(int, size_t) {}
};

struct Client {
	std::map<uint8, uint16> m_class_pets;
	std::array<uint8, 3> classes{13, 11, 10};
	uint16 primary = 101, m_pet_window_id = 101, m_selected_command_pet = 0;
	uint32 m_pet_management_token = 77;
	bool m_pet_management_enabled = true, connected = true;
	Timer m_pet_armor_view_timer;
	Mob* target = nullptr;
	unsigned dispatched = 0;
	uint32 last_command = 0, last_target = 0;
	std::vector<uint16> commanded;
	uint8 m_suspended_pet_class = 0;
	int m_suspendedminion = 0;
	unsigned syncs = 0, publications = 0;
	uint16 GetID() const { return 10; }
	uint16 GetPetID() const { return primary; }
	void SetPetID(uint16 id) { primary = id; }
	Mob* GetPet() { return entity_list.GetMob(primary); }
	bool IsMulticlassMember(uint8 cls) const { return std::find(classes.begin(), classes.end(), cls) != classes.end(); }
	std::array<uint8, 3> GetMulticlassList() const { return classes; }
	uint16 GetClassPet(uint8 cls) const { auto it = m_class_pets.find(cls); return it == m_class_pets.end() ? 0 : it->second; }
	void SyncPetWindow() { ++syncs; m_pet_window_id = primary; }
	void SendPetManagement() { ++publications; }
	bool Connected() const { return connected; }
	Mob* GetTarget() const { return target; }
	void HandlePetArmor(const Seperator* sep);
	void Handle_OP_PetCommands(const EQApplicationPacket* packet) {
		++dispatched;
		auto body = reinterpret_cast<const PetCommand_Struct*>(packet->pBuffer);
		last_command = body->command; last_target = body->target;
		commanded.clear();
		for (auto pet : GetSelectedCommandPets()) commanded.push_back(pet->GetID());
		std::sort(commanded.begin(), commanded.end());
	}
	void UnregisterClassPet(uint16 entity_id);
	std::vector<uint16> GetExtraPetIds() const;
	void RefreshClassPets(bool force_window = false);
	std::vector<NPC*> GetCommandPets();
	std::vector<NPC*> GetSelectedCommandPets();
	bool SelectCommandPet(uint16 id);
	void ObservePetTarget(uint16 id);
};

// ACTUAL_METHODS
// ACTUAL_MANAGEMENT_HANDLER

static void Require(bool condition, const char* message) {
	if (!condition) throw std::runtime_error(message);
}
static std::vector<uint16> Ids(const std::vector<NPC*>& pets) {
	std::vector<uint16> ids;
	for (auto pet : pets) ids.push_back(pet->GetID());
	std::sort(ids.begin(), ids.end());
	return ids;
}
struct Scenario {
	Client owner;
	NPC mage, necro, shaman, foreign, enemy;
	Scenario() {
		mage.id = 101; necro.id = 102; shaman.id = 103;
		foreign.id = 104; foreign.owner = 20;
		enemy.id = 105; enemy.owner = 0;
		entity_list.mobs = {{uint16{101}, &mage}, {uint16{102}, &necro}, {uint16{103}, &shaman}, {uint16{104}, &foreign}, {uint16{105}, &enemy}};
		owner.m_class_pets = {{uint8{13}, uint16{101}}, {uint8{11}, uint16{102}}, {uint8{10}, uint16{103}}};
	}
};

static void SelectionAndClearing() {
	Scenario s;
	Require(Ids(s.owner.GetSelectedCommandPets()) == std::vector<uint16>{101, 102, 103}, "No selection must command all three");
	Require(s.owner.SelectCommandPet(102), "An owned row must be selectable");
	Require(Ids(s.owner.GetSelectedCommandPets()) == std::vector<uint16>{102}, "Selected row must command only its pet");
	Require(Ids(s.owner.GetCommandPets()) == std::vector<uint16>{101, 102, 103}, "Command selection must not filter spell/armor roster");
	s.owner.ObservePetTarget(105);
	Require(Ids(s.owner.GetSelectedCommandPets()) == std::vector<uint16>{102}, "Enemy targeting must retain command selection");
	s.owner.ObservePetTarget(103);
	Require(Ids(s.owner.GetSelectedCommandPets()) == std::vector<uint16>{103}, "Direct owned-pet targeting must select that pet");
	s.owner.ObservePetTarget(0);
	Require(Ids(s.owner.GetSelectedCommandPets()) == std::vector<uint16>{101, 102, 103}, "Clearing target must restore all-pet scope");
	Require(s.owner.SelectCommandPet(101), "Primary can be selected");
	Require(s.owner.SelectCommandPet(0), "All-pets row must clear selection");
	Require(Ids(s.owner.GetSelectedCommandPets()) == std::vector<uint16>{101, 102, 103}, "All-pets row must command all three");
}

static void RejectForeignAndStale() {
	Scenario s;
	Require(s.owner.SelectCommandPet(102), "Select owned pet");
	Require(!s.owner.SelectCommandPet(104), "Foreign pet must not be selectable");
	Require(!s.owner.SelectCommandPet(999), "Missing pet must not be selectable");
	Require(!s.owner.SelectCommandPet(105), "Enemy must not be selectable as controlled pet");
	s.owner.ObservePetTarget(104);
	Require(Ids(s.owner.GetSelectedCommandPets()) == std::vector<uint16>{102}, "Rejected selection must preserve prior valid choice");
	s.necro.owner = 20;
	Require(Ids(s.owner.GetSelectedCommandPets()) == std::vector<uint16>{101, 103}, "Ownership loss must clear stale selection and exclude former pet");
	Require(s.owner.m_selected_command_pet == 0, "Stale selection must be cleared");
	Require(s.owner.m_pet_management_token == 0, "Refresh recovery must invalidate tokens for obsolete roster rows");
}

static void LifecycleAndEntityReuse() {
	Scenario s;
	Require(s.owner.SelectCommandPet(102), "Select departing pet");
	s.owner.UnregisterClassPet(102);
	Require(s.owner.m_selected_command_pet == 0, "Unregistration must immediately clear selection before entity ID reuse");
	Require(s.owner.m_pet_management_token == 0, "Unregistration must invalidate old UI requests before ID reuse");
	NPC replacement; replacement.id = 102;
	entity_list.mobs[102] = &replacement;
	s.owner.m_class_pets[11] = 102;
	Require(Ids(s.owner.GetSelectedCommandPets()) == std::vector<uint16>{101, 102, 103}, "New pet reusing old ID must not inherit individual selection");
	Require(s.owner.SelectCommandPet(103), "Select pet before death");
	s.shaman.dead = true;
	Require(Ids(s.owner.GetSelectedCommandPets()) == std::vector<uint16>{101, 102}, "Dead selected pet must be excluded and restore all scope");
	Require(s.owner.SelectCommandPet(101), "Select primary before depop");
	s.mage.depop = true;
	Require(Ids(s.owner.GetSelectedCommandPets()) == std::vector<uint16>{102}, "Depopped primary must not make surviving pet uncommandable");
	Require(s.owner.GetPetID() == 102, "Survivor must become native representative");
	s.owner.classes = {13, 0, 10};
	Require(s.owner.GetSelectedCommandPets().empty(), "Released class must lose command ownership");
}

static void RefreshRecoveryCannotRetainOldSelection() {
	Scenario s;
	Require(s.owner.SelectCommandPet(103), "Select pet before missing-entity recovery");
	entity_list.mobs.erase(103);
	s.owner.RefreshClassPets();
	Require(s.owner.m_pet_management_token == 0, "Missing-entity recovery must reject stale UI tokens");
	Require(s.owner.m_selected_command_pet == 0, "Refresh must clear departed selection before a later reused ID arrives");
	NPC replacement; replacement.id = 103;
	entity_list.mobs[103] = &replacement;
	s.owner.m_class_pets[10] = 103;
	Require(Ids(s.owner.GetSelectedCommandPets()) == std::vector<uint16>{101, 102, 103}, "Refresh recovery followed by ID reuse must restore all-pet scope");
}

static void ManagementRequestsValidateBeforeDispatch() {
	Scenario s;
	s.owner.target = &s.enemy;
	const Seperator select{3, {"#nightcappet", "select", "102", "77", ""}};
	s.owner.HandlePetArmor(&select);
	Require(s.owner.m_selected_command_pet == 102 && s.owner.m_pet_management_token == 77,
		"Deliberate UI selection must retain token for a quick select/order pair before acknowledgment");
	const Seperator attack{3, {"#nightcappet", "order", "2", "77", ""}};
	s.owner.HandlePetArmor(&attack);
	Require(s.owner.dispatched == 1 && s.owner.last_command == 2 && s.owner.last_target == 105, "Valid UI order must reach native packet handler with combat target");
	Require(s.owner.commanded == std::vector<uint16>{102}, "UI order must retain individually selected recipient");
	for (const char* value : {"", "-1", "+2", "2x", "4294967296", "00000000002", "65536", "34"}) {
		Seperator invalid{3, {"#nightcappet", "order", value, "77", ""}};
		s.owner.HandlePetArmor(&invalid);
	}
	for (const char* value : {"", "0", "-77", "78", "4294967296"}) {
		Seperator invalid{3, {"#nightcappet", "order", "2", value, ""}};
		s.owner.HandlePetArmor(&invalid);
	}
	Require(s.owner.dispatched == 1, "Malformed, stale, and invalid commands must never dispatch");
	s.owner.m_pet_management_enabled = false;
	s.owner.HandlePetArmor(&attack);
	s.owner.m_pet_management_enabled = true;
	s.owner.connected = false;
	s.owner.HandlePetArmor(&attack);
	s.owner.connected = true;
	Require(s.owner.dispatched == 1, "Disabled/disconnected UI session must never dispatch");
	Seperator foreign{3, {"#nightcappet", "select", "104", "77", ""}};
	s.owner.HandlePetArmor(&foreign);
	Require(s.owner.m_selected_command_pet == 102, "Foreign UI selection must preserve owned selection");
	// Missing entity has not yet been observed by periodic reconciliation.
	// The old UI order must not become an all-pets command during dispatch.
	entity_list.mobs.erase(102);
	Seperator dismiss{3, {"#nightcappet", "order", "29", "77", ""}};
	s.owner.HandlePetArmor(&dismiss);
	Require(s.owner.dispatched == 1, "Stale selected-pet order must be rejected before dispatch can broaden it to survivors");
}

int main() {
	try {
		SelectionAndClearing();
		RejectForeignAndStale();
		LifecycleAndEntityReuse();
		RefreshRecoveryCannotRetainOldSelection();
		ManagementRequestsValidateBeforeDispatch();
		std::cout << "Pet command selection controls passed\n";
	} catch (const std::exception& error) {
		std::cerr << error.what() << '\n';
		return 1;
	}
}
