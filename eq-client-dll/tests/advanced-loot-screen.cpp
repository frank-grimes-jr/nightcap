#include "../src/advanced_loot_screen.h"
#include <cassert>
#include <cstdlib>
#include <iostream>

using nightcap::AdvancedLootScreen;
using nightcap::LootScreenAPI;
using nightcap::LootScreenString;
static std::array<void *, 1 + 0x17c / 4> native_storage{};
static void **native_table = native_storage.data() + 1;
static unsigned allocations = 0, destructions = 0, custom_notifies = 0, stock_notifies = 0, frames = 0, stock_frames = 0;
static bool has_xml = true, shown = false, destroyed_visible = false;
static std::string last_text;
static void *control_table = nullptr;
static void *__cdecl Allocate(std::size_t size) { assert(size == 0x220); ++allocations; return std::calloc(1, size); }
static void *__fastcall Construct(void *self, void *, void *parent, const LootScreenString *screen, int flags, int version, const char *block) {
	assert(!parent && !flags && version == 2 && !block);
	assert(std::string(static_cast<const char *>(screen->rep)) == "NightcapAdvancedLootWnd");
	*static_cast<void ***>(self) = native_table;
	*reinterpret_cast<void **>(static_cast<unsigned char *>(self) + 0x1e0) = has_xml ? self : nullptr;
	return self;
}
static void __fastcall Children(void *self, void *) { assert(self == AdvancedLootScreen::Window()); }
static LootScreenString *__fastcall Assign(LootScreenString *self, void *, const char *text) { self->rep = const_cast<char *>(text); return self; }
static void *__fastcall Child(void *self, void *, const LootScreenString *name) {
	assert(self == AdvancedLootScreen::Window());
	return std::string(static_cast<const char *>(name->rep)) == "NCAL_Title" ? &control_table : nullptr;
}
static void *__fastcall Destroy(void *self, void *, unsigned flags) {
	assert(flags == 1 && AdvancedLootScreen::Window() == nullptr);
	assert(*static_cast<void ***>(self) == native_table);
	++destructions; std::free(self); return nullptr;
}
static int __fastcall Notify(void *, void *, void *, uint32_t, void *) { ++stock_notifies; return 23; }
static int __fastcall Frame(void *, void *) { ++stock_frames; return 24; }
static int __fastcall Show(void *self, void *, bool visible, bool top, bool layout) { assert(top == visible && layout); shown = visible; static_cast<unsigned char *>(self)[0x196] = visible; return 0; }
static void __fastcall Text(void *, void *, const LootScreenString *text) { last_text = static_cast<const char *>(text->rep); }
static bool Handle(void *sender, uint32_t message, void *) { ++custom_notifies; return sender == &control_table && message == 1; }
static void Pulse() { ++frames; }
static void Cleared(bool visible) { destroyed_visible = visible; assert(!AdvancedLootScreen::Window()); assert(!AdvancedLootScreen::Create()); }
int main() {
	native_table[1] = reinterpret_cast<void *>(&Destroy);
	native_table[0x88 / 4] = reinterpret_cast<void *>(&Notify);
	native_table[0xc4 / 4] = reinterpret_cast<void *>(&Frame);
	native_table[0xd8 / 4] = reinterpret_cast<void *>(&Show);
	native_table[0x124 / 4] = reinterpret_cast<void *>(&Text);
	native_table[-1] = &allocations; // fake CompleteObjectLocator must be retained
	control_table = native_table;
	LootScreenAPI api{&Allocate, reinterpret_cast<LootScreenAPI::Construct>(&Construct),
		reinterpret_cast<LootScreenAPI::Children>(&Children), reinterpret_cast<LootScreenAPI::Assign>(&Assign),
		reinterpret_cast<LootScreenAPI::Child>(&Child), native_table};
	assert(AdvancedLootScreen::Bind(api, &Handle, &Pulse, &Cleared));
	assert(AdvancedLootScreen::Create());
	alignas(4) unsigned char edit[0x220]{}, rep[96]{};
	*reinterpret_cast<void **>(edit + 0x1ec) = rep;
	char output[33]{};
	for (uint32_t encoding : {0u, 1u}) {
		const auto stride = encoding + 1;
		std::memset(rep, 0, sizeof(rep));
		*reinterpret_cast<uint32_t *>(rep + 4) = 33 * stride;
		*reinterpret_cast<uint32_t *>(rep + 8) = 32;
		*reinterpret_cast<uint32_t *>(rep + 12) = encoding;
		for (unsigned i = 0; i < 32; ++i) { rep[0x14 + i * stride] = 'A'; }
		assert(AdvancedLootScreen::EditText(edit, output) && std::string(output) == std::string(32, 'A'));
		*reinterpret_cast<uint32_t *>(rep + 4) -= 1;
		assert(!AdvancedLootScreen::EditText(edit, output));
		*reinterpret_cast<uint32_t *>(rep + 4) += 1;
		rep[0x14 + 32 * stride] = 'x'; assert(!AdvancedLootScreen::EditText(edit, output));
		rep[0x14 + 32 * stride] = 0;
		rep[0x14] = '\n'; assert(!AdvancedLootScreen::EditText(edit, output));
		rep[0x14] = 'A';
		if (encoding) { rep[0x15] = 1; assert(!AdvancedLootScreen::EditText(edit, output)); }
	}
	AdvancedLootScreen::Destroy(); allocations = destructions = 0;
	for (unsigned iteration = 0; iteration < 1000; ++iteration) {
		assert(AdvancedLootScreen::Create());
		auto self = AdvancedLootScreen::Window();
		auto table = *static_cast<void ***>(self);
		assert(table != native_table && table[-1] == native_table[-1] && !shown);
		assert(!AdvancedLootScreen::Bind(api, &Handle, &Pulse, &Cleared));
		assert(AdvancedLootScreen::Create() && AdvancedLootScreen::Window() == self);
		AdvancedLootScreen::Show(true); assert(shown);
		auto control = AdvancedLootScreen::Child("NCAL_Title"); assert(control == &control_table);
		AdvancedLootScreen::Text(control, "Bone Chips"); assert(last_text == "Bone Chips");
		using Notification = int (__thiscall *)(void *, void *, uint32_t, void *);
		using FrameCall = int (__thiscall *)(void *);
		using DestroyCall = void *(__thiscall *)(void *, unsigned);
		assert(reinterpret_cast<Notification>(table[0x88 / 4])(self, control, 1, nullptr) == 1);
		assert(reinterpret_cast<Notification>(table[0x88 / 4])(self, nullptr, 2, nullptr) == 23);
		assert(reinterpret_cast<FrameCall>(table[0xc4 / 4])(self) == 24);
		// Simulate native UI reload deleting the window through its virtual ABI.
		reinterpret_cast<DestroyCall>(table[1])(self, 1);
		assert(!AdvancedLootScreen::Window() && destroyed_visible);
	}
	assert(allocations == 1000 && destructions == 1000);
	assert(custom_notifies == 2000 && stock_notifies == 1000 && frames == 1000 && stock_frames == 1000);
	has_xml = false; assert(!AdvancedLootScreen::Create());
	assert(allocations == 1001 && destructions == 1001 && !AdvancedLootScreen::Window());
	std::cout << "PASS: native advanced loot screen x86 ABI, callbacks, 1000 reload lifetimes and missing-screen cleanup\n";
}
