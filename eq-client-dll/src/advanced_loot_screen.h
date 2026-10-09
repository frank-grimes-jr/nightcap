#pragma once

#include <array>
#include <cstdint>
#include <cstring>
#include <string>

namespace nightcap {
// Native CSidlScreenWnd ABI for the pinned 2013-05-10 x86 client. These are
// presentation calls only. Install-time guards must validate every entry and
// the native vtable before supplying this interface.
struct LootScreenString { void *rep = nullptr; };
static_assert(sizeof(LootScreenString) == 4, "RoF2 is x86");
struct LootScreenAPI {
	using Allocate = void *(__cdecl *)(std::size_t);
	using Construct = void *(__thiscall *)(void *, void *, const LootScreenString *, int, int, const char *);
	using Children = void (__thiscall *)(void *);
	using Assign = LootScreenString *(__thiscall *)(LootScreenString *, const char *);
	using Child = void *(__thiscall *)(void *, const LootScreenString *);
	Allocate allocate = nullptr;
	Construct construct = nullptr;
	Children children = nullptr;
	Assign assign = nullptr;
	Child child = nullptr;
	void **vtable = nullptr;
};

// The native allocator and native deleting destructor own object memory.
// Only this window's vptr changes; ordinary game windows retain their vtables.
// Calls and callbacks must run on the game UI thread, including destruction on
// skin reload. The proxy is process-pinned, so callback code outlives windows.
class AdvancedLootScreen {
public:
	using Notify = bool (*)(void *sender, uint32_t message, void *data);
	using Frame = void (*)();
	using Destroyed = void (*)();
private:
	using Destructor = void *(__thiscall *)(void *, unsigned);
	using NativeNotify = int (__thiscall *)(void *, void *, uint32_t, void *);
	using NativeFrame = int (__thiscall *)(void *);
	using ShowMethod = int (__thiscall *)(void *, bool, bool, bool);
	using TextMethod = void (__thiscall *)(void *, const LootScreenString *);
	static constexpr std::size_t ObjectSize = 0x220, TableEntries = 0x17c / 4;
	inline static LootScreenAPI api_{};
	// Preserve MSVC's CompleteObjectLocator immediately before the vtable too.
	inline static std::array<void *, TableEntries + 1> table_{};
	inline static void *window_ = nullptr;
	inline static bool destroying_ = false;
	inline static bool broken_ = false;
	inline static Notify notify_ = nullptr;
	inline static Frame frame_ = nullptr;
	inline static Destroyed destroyed_ = nullptr;

	static void *__fastcall DestroyHook(void *self, void *, unsigned flags) {
		// Clear first: a callback or skin reload may otherwise retain a freed
		// window. Forward the exact native deleting flags and allocator path.
		destroying_ = true;
		if (self == window_) { window_ = nullptr; }
		*static_cast<void ***>(self) = api_.vtable;
		if (destroyed_) { destroyed_(); }
		void *result = reinterpret_cast<Destructor>(api_.vtable[1])(self, flags);
		destroying_ = false;
		return result;
	}
	static int __fastcall NotifyHook(void *self, void *, void *sender, uint32_t message, void *data) {
		if (self == window_ && notify_ && notify_(sender, message, data)) { return 1; }
		if (self != window_) { return 1; }
		return reinterpret_cast<NativeNotify>(api_.vtable[0x88 / 4])(self, sender, message, data);
	}
	static int __fastcall FrameHook(void *self, void *) {
		if (self == window_ && frame_) { frame_(); }
		if (self != window_) { return 0; }
		return reinterpret_cast<NativeFrame>(api_.vtable[0xc4 / 4])(self);
	}
public:
	static bool Bind(const LootScreenAPI &api, Notify notify, Frame frame, Destroyed destroyed) {
		if (window_ || destroying_ || !api.allocate || !api.construct || !api.children || !api.assign || !api.child || !api.vtable) { return false; }
		for (const auto index : {1u, 0x88u / 4, 0xc4u / 4, 0xd8u / 4, 0x124u / 4}) {
			if (!api.vtable[index]) { return false; }
		}
		api_ = api; notify_ = notify; frame_ = frame; destroyed_ = destroyed; broken_ = false;
		std::memcpy(table_.data(), api_.vtable - 1, sizeof(table_));
		table_[2] = reinterpret_cast<void *>(&DestroyHook);
		table_[1 + 0x88 / 4] = reinterpret_cast<void *>(&NotifyHook);
		table_[1 + 0xc4 / 4] = reinterpret_cast<void *>(&FrameHook);
		return true;
	}
	static void *Window() { return window_; }
	static bool Broken() { return broken_; }
	static bool Create() {
		if (window_) { return true; }
		if (destroying_ || broken_ || !api_.allocate) { return false; }
		void *storage = api_.allocate(ObjectSize);
		if (!storage) { return false; }
		LootScreenString name{};
		api_.assign(&name, "NightcapAdvancedLootWnd");
		void *created = api_.construct(storage, nullptr, &name, 0, 2, nullptr);
		api_.assign(&name, "");
		if (created != storage || *static_cast<void ***>(created) != api_.vtable) {
			// This contradicts the pinned constructor contract. Do not free or
			// dereference an unknown registered UI object; caller must stop setup.
			broken_ = true;
			return false;
		}
		window_ = created;
		*static_cast<void ***>(window_) = table_.data() + 1;
		if (!*reinterpret_cast<void **>(static_cast<unsigned char *>(window_) + 0x1e0)) {
			Destroy(); // XML screen missing: native destructor unregisters it
			return false;
		}
		api_.children(window_);
		Show(false);
		return true;
	}
	static void Destroy() {
		if (window_ && !destroying_) { DestroyHook(window_, nullptr, 1); }
	}
	static void Show(bool visible) {
		if (window_) { reinterpret_cast<ShowMethod>(api_.vtable[0xd8 / 4])(window_, visible, visible, true); }
	}
	static void *Child(const std::string &id) {
		if (!window_ || id.empty() || id.size() > 63) { return nullptr; }
		LootScreenString name{};
		api_.assign(&name, id.c_str());
		void *child = api_.child(window_, &name);
		api_.assign(&name, "");
		return child;
	}
	static void Text(void *control, const std::string &text) {
		if (!window_ || !control || text.size() > 256) { return; }
		LootScreenString value{};
		api_.assign(&value, text.c_str());
		const auto table = *static_cast<void ***>(control);
		reinterpret_cast<TextMethod>(table[0x124 / 4])(control, &value);
		api_.assign(&value, "");
	}
	static void Enable(void *control, bool enabled) {
		// CXWnd::Enabled, pinned by the exact May 2013 class layout.
		if (window_ && control) { *reinterpret_cast<bool *>(static_cast<unsigned char *>(control) + 0x1a) = enabled; }
	}
	static void Visible(void *control, bool visible) {
		if (!window_ || !control) { return; }
		if (*reinterpret_cast<bool *>(static_cast<unsigned char *>(control) + 0x196) == visible) { return; }
		const auto table = *static_cast<void ***>(control);
		reinterpret_cast<ShowMethod>(table[0xd8 / 4])(control, visible, false, true);
	}
	static bool Visible() {
		// CXWnd::dShow, see the native layout used by the proxy.
		return window_ && *reinterpret_cast<bool *>(static_cast<unsigned char *>(window_) + 0x196);
	}
	static bool EditText(void *control, char (&output)[33]) {
		// CEditBaseWnd::InputText at 0x1ec. Read only a bounded ASCII CXStr,
		// rejecting tagged/Unicode input. Never retain its native buffer.
		if (!window_ || !control) { return false; }
		__try {
			const auto rep = *reinterpret_cast<const unsigned char **>(static_cast<unsigned char *>(control) + 0x1ec);
			if (!rep) { output[0] = 0; return true; }
			const auto length = *reinterpret_cast<const uint32_t *>(rep + 8);
			if (*reinterpret_cast<const uint32_t *>(rep + 12) != 0 || length > 32 ||
				*reinterpret_cast<const uint32_t *>(rep + 4) <= length || rep[0x14 + length] != 0) { return false; }
			for (uint32_t i = 0; i < length; ++i) {
				if (rep[0x14 + i] < 32 || rep[0x14 + i] > 126) { return false; }
				output[i] = static_cast<char>(rep[0x14 + i]);
			}
			output[length] = 0;
			return true;
		} __except(1) { return false; }
	}
	static void EditLimit(void *control) {
		if (!window_ || !control) { return; }
		// CEditBaseWnd::MaxChars / MaxBytesUTF8; SIDL has no MaxChars element.
		*reinterpret_cast<int *>(static_cast<unsigned char *>(control) + 0x1e4) = 32;
		*reinterpret_cast<int *>(static_cast<unsigned char *>(control) + 0x1e8) = 32;
	}
};
}
