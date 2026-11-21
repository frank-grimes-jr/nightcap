#pragma once
#include <cstdint>
#include <string_view>
#include "../../server-mods/code/common/dungeon_catalog.h"

namespace nightcap {
inline constexpr uint32_t RegularItemColor = 0xff00ff00;
inline constexpr uint32_t PolishedItemColor = 0xff0070dd;
inline constexpr uint32_t ExaltedItemColor = 0xffa335ee;
inline constexpr uint32_t AscendedItemColor = 0xffff8000;

// Pinned RoF2 CXWnd label color and CButtonWnd hover/pressed text colors.
// Only pass known item-name controls. Keep the disabled color at +0x218 native.
inline void SetItemNameTextColor(void* control, uint32_t color, bool button = false) {
    if (!control) return;
    auto bytes = static_cast<unsigned char*>(control);
    *reinterpret_cast<uint32_t*>(bytes+0x12c) = color;
    if (button) {
        *reinterpret_cast<uint32_t*>(bytes+0x210) = color;
        *reinterpret_cast<uint32_t*>(bytes+0x214) = color;
    }
}

// Use explicit quality markers, not broad item-ID bands. Hunt, dungeon and
// ordinary upgrades have different ID layouts. Natural names such as Polished
// Granite Tomahawk are regular items. Pass the undecorated definition/row name.
inline uint32_t ItemNameColor(uint32_t id, std::string_view name) {
    if (!id || id > 1048575 || name.empty() || name.size() > 63) return RegularItemColor;
    const auto suffix = [&](std::string_view marker) {
        return name.size() > marker.size() && name.substr(name.size()-marker.size()) == marker;
    };
    if (suffix(" (Polished)")) return PolishedItemColor;
    if (suffix(" (Exalted)")) return ExaltedItemColor;
    if (suffix(" (Ascended)") || suffix(" (Ascension)")) return AscendedItemColor;
    // Dungeon quality is a prefix; restrict it to the catalog's reward range.
    constexpr uint32_t dungeon_begin = 960000;
    constexpr uint32_t dungeon_end = dungeon_begin + 24*4*3 + NightcapDungeon::DungeonCount*3*2;
    if (id >= dungeon_begin && id < dungeon_end) {
        if (name.size() > 9 && name.substr(0,9) == "Polished ") return PolishedItemColor;
        if (name.size() > 9 && name.substr(0,9) == "Ascended ") return AscendedItemColor;
    }
    return RegularItemColor;
}

inline uint32_t InspectionItemNameColor(uint32_t native_color, uint32_t id, std::string_view name) {
    // Preserve native red/unmet-requirement warnings. Our colors can be present
    // on another description refresh, so allow them to be recomputed too.
    if (native_color == RegularItemColor || native_color == PolishedItemColor ||
        native_color == ExaltedItemColor || native_color == AscendedItemColor)
        return ItemNameColor(id,name);
    return native_color;
}
}
