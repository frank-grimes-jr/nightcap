#pragma once
#include <array>
#include <cstdint>
#include <map>
#include <string>
#include <string_view>

namespace nightcap {
class PetState {
    struct Slot { uint32_t item = 0; std::string name; };
    struct Pet {
        uint32_t spawn = 0;
        std::string name;
        std::array<Slot, 22> slots{};
        uint32_t received = 0;
    };
    struct Snapshot {
        std::array<uint32_t, 5> identity{}; // nonce, character, zone, instance, spawn
        std::string name;
        std::map<uint32_t, Pet> pets;
    } current_, pending_;
    bool receiving_ = false;
    uint32_t selected_ = 0;
    unsigned page_ = 0;
    static bool Number(std::string_view text, uint32_t &value) {
        if (text.empty() || text.size() > 10) return false;
        value = 0;
        for (char c : text) {
            if (c < '0' || c > '9' || value > (UINT32_MAX - (c - '0')) / 10) return false;
            value = value * 10 + (c - '0');
        }
        return true;
    }
    static bool Decode(std::string_view hex, std::string &value) {
        if (hex.empty() || hex.size() > 126 || hex.size() % 2) return false;
        auto digit = [](char c) -> int { return c >= '0' && c <= '9' ? c-'0' : c >= 'a' && c <= 'f' ? c-'a'+10 : -1; };
        value.clear();
        for (size_t i = 0; i < hex.size(); i += 2) {
            const int a = digit(hex[i]), b = digit(hex[i+1]);
            if (a < 0 || b < 0) return false;
            const char c = static_cast<char>(a*16+b);
            if (c < 32 || c > 126) return false;
            value += c;
        }
        return true;
    }
    const Pet *Selected() const {
        const auto found = current_.pets.find(selected_);
        return found == current_.pets.end() ? nullptr : &found->second;
    }
public:
    void Clear() { current_ = {}; pending_ = {}; receiving_ = false; selected_ = 0; page_ = 0; }
    void NextPage(int direction) {
        if (!receiving_) page_ = (page_ + (direction < 0 ? 2 : 1)) % 3;
    }
    bool Matches(uint32_t spawn, const char *name) const {
        return !receiving_ && current_.identity[0] && current_.identity[4] == spawn && name && current_.name == name;
    }
    uint32_t SelectedClass() const { return selected_; }
    uint32_t Nonce() const { return receiving_ ? 0 : current_.identity[0]; }
    void Next(int direction) {
        if (current_.pets.empty() || receiving_) return;
        auto it = current_.pets.find(selected_);
        if (it == current_.pets.end()) it = current_.pets.begin();
        else if (direction < 0) { if (it == current_.pets.begin()) it = current_.pets.end(); --it; }
        else { if (++it == current_.pets.end()) it = current_.pets.begin(); }
        selected_ = it->first;
    }
    std::string TitleText() const {
        static constexpr const char *classes[] = {"", "WAR", "CLR", "PAL", "RNG", "SHD", "DRU", "MNK", "BRD", "ROG", "SHM", "NEC", "WIZ", "MAG", "ENC", "BST", "BER"};
        const auto pet = Selected();
        unsigned used = 0;
        if (pet) for (const auto &slot : pet->slots) used += slot.item != 0;
        return pet ? std::string(classes[selected_]) + " " + std::to_string(used) + "/" +
            (selected_ == 13 ? "15" : "8") + " - " + pet->name + (pet->spawn ? "" : " (inactive)") : "No owned pets or stored equipment";
    }
    std::string SlotText(unsigned index) const {
        static constexpr const char *names[] = {"Head", "Chest", "Arms", "Wrist 1", "Hands", "Legs", "Feet", "Waist",
            "Primary", "Secondary", "Ear 1", "Ear 2", "Neck", "Face", "Shoulders", "Back",
            "Wrist 2", "Finger 1", "Finger 2", "Range", "Charm", "Power source"};
        if (index >= 8) return "";
        index += page_ * 8;
        if (index >= 22) return "";
        const auto pet = Selected();
        return std::string(names[index]) + ": " + (pet ? pet->slots[index].name : "Empty");
    }
    std::string Command(const char *action, unsigned index) const {
        if (!action || receiving_ || !current_.identity[0] || index >= 8) return "";
        index += page_ * 8;
        if (index >= 22) return "";
        const auto pet = Selected();
        if (!pet) return "";
        const std::string verb(action);
        if (verb == "equip") { if (!pet->spawn || pet->slots[index].item) return ""; }
        else if (verb == "remove" || verb == "inspect") { if (!pet->slots[index].item) return ""; }
        else return "";
        return "#nightcappet " + verb + " " + std::to_string(selected_) + " " + std::to_string(index) + " " + std::to_string(current_.identity[0]);
    }
    bool Consume(const char *message) {
        if (!message) return false;
        size_t size = 0;
        while (size < 256 && message[size]) ++size;
        if (size < 10 || size == 256) return false;
        const std::string_view text(message, size);
        if (text.substr(0,7) != "[NCPA2]" || text[8] != '|') return false;
        const char type = text[7];
        const unsigned expected = type == 'B' ? 6 : type == 'P' ? 4 : type == 'I' ? 5 : type == 'E' ? 1 : 0;
        if (!expected) return false;
        std::array<std::string_view, 6> fields{};
        size_t start = 9, count = 0;
        while (start <= size) {
            if (count == fields.size()) return false;
            auto end = text.find('|', start);
            if (end == std::string_view::npos) end = size;
            fields[count++] = text.substr(start,end-start); start = end+1;
        }
        if (count != expected) return false;
        std::array<uint32_t, 5> values{};
        for (unsigned i = 0; i < (type == 'E' ? 1 : expected-1); ++i) {
            if (!Number(fields[i], values[i])) return false;
        }
        if (!values[0]) return false;
        std::string name;
        if (type != 'E' && !Decode(fields[expected-1], name)) return false;
        if (type == 'B') {
            if (!values[1] || !values[2] || !values[4] || values[4] > 65535) return false;
            const auto &old = receiving_ ? pending_ : current_;
            bool same = true;
            for (unsigned i = 1; i < 5; ++i) same = same && old.identity[i] == values[i];
            if (same && old.identity[0] >= values[0]) return false;
            pending_ = {}; pending_.identity = values; pending_.name = std::move(name); receiving_ = true;
            return true;
        }
        if (!receiving_ || values[0] != pending_.identity[0]) return false;
        if (type == 'E') {
            for (const auto &entry : pending_.pets) if (entry.second.received != ((1u << 22) - 1)) return false;
            current_ = std::move(pending_); pending_ = {}; receiving_ = false;
            if (!current_.pets.count(selected_)) selected_ = current_.pets.empty() ? 0 : current_.pets.begin()->first;
            return true;
        }
        if (values[1] < 1 || values[1] > 16) return false;
        if (type == 'P') {
            if (values[2] > 65535 || pending_.pets.count(values[1])) return false;
            auto &pet = pending_.pets[values[1]]; pet.spawn = values[2]; pet.name = std::move(name);
            return true;
        }
        auto pet = pending_.pets.find(values[1]);
        if (pet == pending_.pets.end() || values[2] >= 22 || (pet->second.received & (1u << values[2]))) return false;
        pet->second.slots[values[2]] = {values[3], std::move(name)};
        pet->second.received |= 1u << values[2];
        return true;
    }
};
}
