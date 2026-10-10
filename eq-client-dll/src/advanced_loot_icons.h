#pragma once
#include <cstdint>

namespace nightcap {
// Pinned May 10 2013 RoF2 presentation ABI. The item cache owns these
// animations, just as it does for native inventory and item-display buttons.
// Never change their current cell or free them from an individual window.
class AdvancedLootIcons {
public:
	using Cache = void *(__cdecl *)(int);
	using Get = void *(__thiscall *)(void *, int);
	inline static Cache cache = nullptr;
	inline static Get get = nullptr;
	static bool Set(void *button, uint32_t icon) {
		if (!button) { return false; }
		void *animation = nullptr;
		if (icon && icon <= 0x7fffffff && cache && get) {
			void *items = cache(0); // eIconCacheType::eit_Items
			if (items) {
				const auto bytes = static_cast<const unsigned char *>(items);
				const int minimum = *reinterpret_cast<const int *>(bytes + 0x18);
				const int maximum = *reinterpret_cast<const int *>(bytes + 0x1c);
				// Native GetIcon clamps invalid IDs to the first icon. Hide them
				// instead of showing an unrelated item's image.
				if (minimum >= 0 && maximum >= minimum && icon >= static_cast<uint32_t>(minimum) && icon <= static_cast<uint32_t>(maximum)) {
					animation = get(items, static_cast<int>(icon));
				}
			}
		}
		for (unsigned offset = 0x240; offset <= 0x254; offset += 4) {
			*reinterpret_cast<void **>(static_cast<unsigned char *>(button) + offset) = animation;
		}
		return animation != nullptr;
	}
};
}
