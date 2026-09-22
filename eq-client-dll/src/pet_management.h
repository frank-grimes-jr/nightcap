#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace nightcap {
// Server-acknowledged command selection is independent of inventory armor selection.
class PetManagement {
    struct Row { uint32_t cls = 0, spawn = 0, hp = 0; std::string name; };
    std::array<Row, 3> rows_{};
    uint32_t token_ = 0, generation_ = 0, character_ = 0, zone_ = 0, instance_ = 0;
    uint32_t owner_ = 0, selected_ = 0, count_ = 0;
    std::string name_;
    static bool Number(std::string_view text, uint32_t& result) {
        if (text.empty() || text.size() > 10) return false;
        result = 0;
        for (char c : text) {
            if (c < '0' || c > '9' || result > (UINT32_MAX - (c-'0')) / 10) return false;
            result = result*10 + c-'0';
        }
        return true;
    }
    static bool Name(std::string_view text, std::string& result) {
        if (text.empty() || text.size() > 126 || text.size()%2) return false;
        auto digit = [](char c) { return c >= '0' && c <= '9' ? c-'0' : c >= 'a' && c <= 'f' ? c-'a'+10 : -1; };
        result.clear();
        for (size_t i = 0; i < text.size(); i += 2) {
            const int a = digit(text[i]), b = digit(text[i+1]);
            if (a < 0 || b < 0 || a*16+b < 32 || a*16+b > 126) return false;
            result += static_cast<char>(a*16+b);
        }
        return true;
    }
    std::string Selection(uint32_t spawn) const {
        return token_ ? "#nightcappet select " + std::to_string(spawn) + " " + std::to_string(token_) : "";
    }
public:
    void Clear() { *this = {}; }
    bool Matches(uint32_t owner, const char* name) const { return token_ && owner_ == owner && name && name_ == name; }
    bool HasPets() const { return count_ != 0; }
    std::string AllCommand() const { return Selection(0); }
    std::string OrderCommand(unsigned command) const {
        return token_ && count_ && command < 34 ? "#nightcappet order " + std::to_string(command) + " " + std::to_string(token_) : "";
    }
    std::string SelectCommand(unsigned row) const {
        return row < count_ ? Selection(rows_[row].spawn == selected_ ? 0 : rows_[row].spawn) : "";
    }
    std::string ScopeText() const {
        for (unsigned i = 0; i < count_; ++i) if (rows_[i].spawn == selected_) return "Commands: " + rows_[i].name;
        return "Commands: All pets";
    }
    std::string RowText(unsigned row) const {
        static constexpr const char* classes[] = {"", "WAR", "CLR", "PAL", "RNG", "SHD", "DRU", "MNK", "BRD", "ROG", "SHM", "NEC", "WIZ", "MAG", "ENC", "BST", "BER"};
        if (row >= count_) return "No pet summoned";
        const auto& pet = rows_[row];
        return std::string(pet.spawn == selected_ ? "> " : "") + classes[pet.cls] + "  " + pet.name + "  " + std::to_string(pet.hp) + "%";
    }
    bool Consume(const char* message) {
        if (!message) return false;
        size_t size = 0;
        while (size < 768 && message[size]) ++size;
        const std::string_view text(message, size);
        if (size == 768 || text.substr(0,8) != "[NCPM1]|") return false;
        std::array<std::string_view, 21> fields{};
        size_t start = 8, count = 0;
        while (start <= size) {
            if (count == fields.size()) return false;
            auto end = text.find('|', start);
            if (end == std::string_view::npos) end = size;
            fields[count++] = text.substr(start, end-start); start = end+1;
        }
        if (count < 9) return false;
        PetManagement next;
        uint32_t* numbers[] = {&next.token_, &next.generation_, &next.character_, &next.zone_, &next.instance_, &next.owner_};
        for (unsigned i = 0; i < 6; ++i) if (!Number(fields[i], *numbers[i])) return false;
        if (!Name(fields[6], next.name_) || !Number(fields[7], next.selected_) || !Number(fields[8], next.count_) ||
            !next.token_ || !next.generation_ || !next.character_ || !next.zone_ || !next.owner_ || next.owner_ > 65535 ||
            next.count_ > 3 || count != 9 + next.count_*4) return false;
        if (token_ && character_ == next.character_ && owner_ == next.owner_ &&
            zone_ == next.zone_ && instance_ == next.instance_ && next.generation_ <= generation_) return false;
        bool selected_found = next.selected_ == 0;
        for (unsigned i = 0; i < next.count_; ++i) {
            auto& row = next.rows_[i];
            const unsigned index = 9+i*4;
            if (!Number(fields[index], row.cls) || !Number(fields[index+1], row.spawn) || !Number(fields[index+2], row.hp) ||
                !Name(fields[index+3], row.name) || row.cls < 1 || row.cls > 16 || !row.spawn || row.spawn > 65535 || row.hp > 100) return false;
            for (unsigned j = 0; j < i; ++j) if (next.rows_[j].cls == row.cls || next.rows_[j].spawn == row.spawn) return false;
            selected_found = selected_found || next.selected_ == row.spawn;
        }
        if (!selected_found) return false;
        *this = std::move(next);
        return true;
    }
};
}
