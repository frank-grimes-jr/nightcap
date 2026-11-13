#pragma once
#include "../../server-mods/code/common/inventory_stats_protocol.h"

namespace nightcap {
class InventoryStatsState {
    NightcapInventory::Snapshot snapshot_{};
    uint64_t received_ = 0;
    bool valid_ = false;
public:
    static bool Handles(int type) {
        return (type >= 10500 && type < 10505) || (type >= 10600 && type < 10607) ||
            (type >= 10700 && type < 10707) || (type >= 10800 && type < 10807);
    }
    void Clear() { snapshot_ = {}; received_ = 0; valid_ = false; }
    bool Consume(const char* message, const NightcapInventory::Identity& identity, uint64_t now) {
        NightcapInventory::Snapshot next;
        if (!NightcapInventory::Decode(message, next) || next.identity != identity) return false;
        if (valid_ && snapshot_.identity == identity && static_cast<int32_t>(next.sequence - snapshot_.sequence) <= 0) return false;
        snapshot_ = next; received_ = now; valid_ = true; return true;
    }
    bool Ready(const NightcapInventory::Identity& identity, uint64_t now) const {
        return valid_ && snapshot_.identity == identity && now >= received_ && now - received_ < 8000;
    }
    std::string Label(int type, const NightcapInventory::Identity& identity, uint64_t now) const {
        if (!Ready(identity, now)) return "--";
        const auto& v = snapshot_.values;
        if (type >= 10500 && type < 10505) {
            const auto value = v[type - 10500];
            return type == 10501 && value == -1 ? "Auto" : std::to_string(value);
        }
        if (type >= 10600 && type < 10607) return std::to_string(v[NightcapInventory::Strength + type - 10600]);
        if (type >= 10800 && type < 10807) return "/" + std::to_string(v[NightcapInventory::StrengthCap + type - 10800]);
        if (type >= 10700 && type < 10707) {
            const auto value = v[NightcapInventory::HeroicStrength + type - 10700];
            return (value >= 0 ? "+" : "") + std::to_string(value);
        }
        return "--";
    }
    uint32_t Color(int type, const NightcapInventory::Identity& identity, uint64_t now) const {
        if (!Ready(identity, now)) return 0xFFAAAAAA;
        if (type >= 10700 && type < 10707) return 0xFFD6B228;
        if (type >= 10800 && type < 10807) return 0xFFFFFFFF;
        return 0xFF00FF00;
    }
};
}
