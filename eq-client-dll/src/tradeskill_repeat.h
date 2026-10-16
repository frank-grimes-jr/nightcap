#pragma once
#include <cstdint>

namespace nightcap {
// The completion marker is a bounded, unsigned protocol, not chat free text.
inline bool ParseTradeskillReply(const char* text, uint32_t& spawn, uint32_t& recipe, bool& attempted) {
    const char prefix[] = "[NCTS1]|";
    if (!text) return false;
    for (unsigned i = 0; i < sizeof(prefix) - 1; ++i)
        if (text[i] != prefix[i]) return false;
    text += sizeof(prefix) - 1;
    uint32_t fields[3] = {};
    for (unsigned field = 0; field < 3; ++field) {
        unsigned digits = 0;
        while (*text >= '0' && *text <= '9') {
            const uint32_t digit = *text++ - '0';
            if (++digits > 10 || fields[field] > (UINT32_MAX - digit) / 10) return false;
            fields[field] = fields[field] * 10 + digit;
        }
        if (!digits || *text != (field == 2 ? '\0' : '|')) return false;
        if (field != 2) ++text;
    }
    if (!fields[0] || !fields[1] || fields[2] > 1) return false;
    spawn = fields[0]; recipe = fields[1]; attempted = fields[2] != 0;
    return true;
}
// One outstanding native operation. Stopping does not erase that operation;
// uncertain completion blocks another run until a new game session.
class TradeskillRepeat {
    enum class Phase { Idle, Waiting, Inventory, Draining };
    Phase phase_ = Phase::Idle;
    bool active_ = false, uncertain_ = false;
    uint32_t spawn_ = 0, recipe_ = 0, completed_ = 0;
    uint64_t sent_ = 0, next_ = 0, deadline_ = 0;
public:
    enum class Action { None, Craft, Inventory, Stopped };
    bool Active() const { return active_; }
    bool Pending() const { return phase_ == Phase::Waiting; }
    bool Uncertain() const { return uncertain_; }
    uint32_t Completed() const { return completed_; }
    void Reset() { *this = TradeskillRepeat{}; }
    void Stop() { active_ = false; if (!Pending()) phase_ = Phase::Idle; }
    void NotDispatched() { active_ = false; phase_ = Phase::Idle; }
    bool Start(uint64_t now, uint32_t spawn, uint32_t recipe) {
        if (active_ || uncertain_ || Pending() || !spawn || !recipe) return false;
        active_ = true; spawn_ = spawn; recipe_ = recipe; completed_ = 0;
        phase_ = Phase::Waiting; sent_ = now;
        return true;
    }
    bool Ack(uint64_t, uint32_t spawn, uint32_t recipe, bool attempted) {
        if (!Pending() || spawn != spawn_ || recipe != recipe_) return false;
        phase_ = Phase::Idle;
        if (!active_ || !attempted) { active_ = false; return true; }
        ++completed_; phase_ = Phase::Inventory; next_ = sent_ + 2200;
        return true;
    }
    Action Pulse(uint64_t now, bool ready, bool same_context) {
        if (Pending() && now - sent_ >= 15000) {
            Stop(); uncertain_ = true; phase_ = Phase::Idle;
            return Action::Stopped;
        }
        if (!active_) return Action::None;
        if (!same_context) { Stop(); return Action::Stopped; }
        if (phase_ == Phase::Waiting || now < next_) return Action::None;
        if (phase_ == Phase::Inventory) {
            phase_ = Phase::Draining; deadline_ = now + 5000; next_ = now + 300;
            return Action::Inventory;
        }
        if (phase_ == Phase::Draining) {
            if (ready) { phase_ = Phase::Waiting; sent_ = now; return Action::Craft; }
            if (now >= deadline_) { Stop(); return Action::Stopped; }
            next_ = now + 300; return Action::Inventory;
        }
        return Action::None;
    }
};
}
