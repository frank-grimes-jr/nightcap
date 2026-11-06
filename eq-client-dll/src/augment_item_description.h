#pragma once
#include <string>
#pragma push_macro("min")
#pragma push_macro("max")
#undef min
#undef max
#include "../../server-mods/code/common/zone_hunt_policy.h"
#pragma pop_macro("max")
#pragma pop_macro("min")

namespace nightcap {
// Same policy as the server's strongest-only equipped shield-block helper.
// This is a property description, not a claim that a bagged/training item is active.
inline std::string AugmentItemDescription(const char* original, uint32_t id) {
    std::string text = original ? original : "";
    constexpr const char* marker = "<BR><c \"#00FFFF\">Hunt Shield Block";
    const auto previous = text.find(marker);
    if (previous != std::string::npos) text.erase(previous);
    const int block = NightcapHunt::AugmentShieldBlock(id);
    if (!block) return text;
    text += marker;
    text += "</c><BR>Shield Block: +" + std::to_string(block) + "% (not Shielding).<BR>";
    text += "Requires this augment socketed in worn armor and a usable shield equipped.<BR>";
    text += "Only the strongest Hunt shield-block augment applies.<BR>";
    text += "View equipped totals on Inventory's Stats tab.<BR>";
    return text;
}
}
