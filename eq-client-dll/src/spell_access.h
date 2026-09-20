#pragma once
#include "../../server-mods/code/common/spell_class_catalog.h"

namespace nightcap {
inline uint8_t HeldSpellLevel(uint32_t spell, uint32_t classes) {
    uint8_t best = 255;
    for (unsigned id = 1; id <= 16; ++id) {
        if (!(classes & (uint32_t(1) << (id - 1)))) continue;
        const auto level = NightcapSpellClasses::Level(spell, id);
        if (level < best) best = level;
    }
    return best;
}
inline uint32_t MerchantClassMask(uint32_t stock, uint32_t primary, uint32_t held,
    bool scroll, uint32_t spell) {
    // A native zero can express additional item restrictions; never override it.
    if (!stock || primary < 1 || primary > 16) return stock;
    const uint32_t eligible = scroll ? NightcapSpellClasses::Mask(spell) : stock;
    return eligible | ((eligible & held) ? uint32_t(1) << (primary - 1) : 0);
}
}
