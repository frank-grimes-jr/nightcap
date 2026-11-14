#include <any>
#include <array>
#include <cassert>
#include <vector>

enum class AugmentActions { Remove, Swap };
namespace Chat { enum { Red, Yellow }; }
namespace EQ {
namespace item { enum { ItemTypeAugmentationDistiller = 56, ItemTypePerfectedAugmentationDistiller = 64 }; }
namespace textures { enum { materialInvalid = 255 }; }
namespace invslot { enum { slotCursor = 33 }; }
}

enum { EVENT_UNAUGMENT_ITEM, EVENT_AUGMENT_REMOVE, EVENT_AUGMENT_REMOVE_CLIENT };
struct Events {
	template<class... Args> bool ItemHasQuestSub(Args...) { return false; }
	template<class... Args> bool PlayerHasQuestSub(Args...) { return false; }
	template<class... Args> void EventItem(Args&&...) {}
	template<class... Args> void EventPlayer(Args&&...) {}
};
namespace fmt { template<class... Args> int format(Args...) { return 0; } }
template<class... Args> void LogError(Args...) {}
template<class... Args> void Message(Args...) {}

struct Item {
	int ID, ItemType, AugDistiller, quantity;
	Item* socket = nullptr;
	Item* GetItem() { return this; }
	int GetID() const { return ID; }
	Item* GetAugment(int index) const { return index == 0 ? socket : nullptr; }
	Item* RemoveAugment(int index) {
		assert(index == 0);
		auto removed = socket;
		socket = nullptr;
		return removed;
	}
	Item* Clone() const { return new Item(*this); }
	bool IsStackable() const { return ItemType == 64 || ItemType == 56; }
	void UpdateOrnamentationInfo() {}
};

struct Inventory {
	static constexpr int item_slot = 23, solvent_slot = 24;
	std::array<Item, 34> slots{};
	Events events;
	Events* parse = &events;
	struct Packet { AugmentActions augment_action = AugmentActions::Remove; int augment_index = 0; };
	void DeleteItemInInventory(int slot, int units, bool) {
		if (units && slots[slot].quantity > units) slots[slot].quantity -= units;
		else slots[slot] = {};
	}
	bool PutItemInInventory(int slot, const Item& item, bool) {
		assert(slots[slot].ID == 0);
		slots[slot] = item;
		return true;
	}
	void CalcBonuses() {}
	void SendWearChange(int) {}
	void remove(int material = EQ::textures::materialInvalid) {
		const Packet packet{};
		const auto* in_augment = &packet;
		auto* tobe_auged = &slots[item_slot];
		Item* solvent = slots[solvent_slot].ID ? &slots[solvent_slot] : nullptr;
		Item *old_aug = nullptr, *aug = nullptr, *item_one_to_push = nullptr, *item_two_to_push = nullptr;
		[[maybe_unused]] const bool update_ornamentation = false;
		// DISTILLER_GATE
		switch (packet.augment_action) {
			// REMOVE_CASE
			default: assert(false);
		}
		delete item_one_to_push;
		delete item_two_to_push;
	}
};

void run_case(int required, int supplied, int type, int quantity, bool success) {
	Inventory inv;
	Item eye{51904,54,required,1};
	inv.slots[23] = {1001,0,0,1,&eye};
	inv.slots[24] = {supplied,type,0,quantity};
	inv.remove();
	assert(inv.slots[23].ID == 1001);
	assert(inv.slots[23].socket == (success ? nullptr : &eye));
	assert(inv.slots[33].ID == (success ? eye.ID : 0));
	assert(inv.slots[33].quantity == (success ? 1 : 0));
	assert(inv.slots[24].quantity == quantity - (success && supplied ? 1 : 0));
}

int main() {
	run_case(47004,52023,64,2,true);  // Eye with Della's perfected distiller
	run_case(47004,52023,64,1,true);
	run_case(47004,47004,56,1,true);
	run_case(47004,47001,56,1,false);
	run_case(47004,47000,55,1,false);
	run_case(47004,0,0,0,false);
	run_case(0,0,0,0,true);
}
