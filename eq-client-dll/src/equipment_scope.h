#pragma once
#include <cstdint>

namespace nightcap {
// Local to the calling thread and active item. Never stored in client item data.
inline const void*& ActiveEquipItem() {
    static thread_local const void* item = nullptr;
    return item;
}
inline const void* SetActiveEquipItem(const void* item) {
    const void* previous = ActiveEquipItem();
    ActiveEquipItem() = item;
    return previous;
}
inline uint32_t EquipClassMask(uint32_t stock, const void* item, bool flag1, bool flag2) {
    // Exact flags at the proven CanUseItem call site. Preserve a zero mask:
    // the native accessor also returns zero for unusable item/augment states.
    if (stock && item && item == ActiveEquipItem() && flag1 && !flag2) {
        return stock | 0xFFFFu;
    }
    return stock;
}
} // namespace nightcap
