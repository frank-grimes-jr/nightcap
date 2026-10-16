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
inline uint32_t EquipClassMask(uint32_t stock, const void* item, bool flag1, bool flag2,
    uint32_t primary, uint32_t held) {
    // Exact flags at the proven CanUseItem call site. Preserve a zero mask:
    // the native accessor also returns zero for unusable item/augment states.
    // CanEquipItem also supplies inspection colors. Project only held classes
    // onto the primary class tested by native CanUseItem.
    if (stock && item && item == ActiveEquipItem() && flag1 && !flag2 &&
        primary >= 1 && primary <= 16 && (held & (1u << (primary - 1))) && (stock & held)) {
        return stock | (1u << (primary - 1));
    }
    return stock;
}
} // namespace nightcap
