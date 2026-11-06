#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <string_view>
#include <unordered_map>
#include "../../server-mods/code/common/aa_recommendations.h"

namespace nightcap {
// Presentation metadata only. Never use this cache to authorize purchases,
// class changes or item transfers. All methods run on the client's UI thread.
class UIState {
    std::array<uint32_t, 5> identity_{}; // generation, character, zone, instance, spawn
    std::array<uint32_t, 3> classes_{};
    std::string name_;
    std::unordered_map<uint32_t, uint32_t> aa_classes_;
    struct RecommendationRow { uint32_t reason, status, target; };
    std::unordered_map<uint32_t, RecommendationRow> recommended_, pending_recommended_;
    bool recommendations_ready_ = false, recommendations_pending_ = false;
    uint32_t recommendations_expected_ = 0;
    void ClearRecommendations() {
        recommended_.clear(); pending_recommended_.clear();
        recommendations_ready_ = recommendations_pending_ = false;
    }
    static constexpr const char* names_[17] = {
        "---","WAR","CLR","PAL","RNG","SHD","DRU","MNK","BRD",
        "ROG","SHM","NEC","WIZ","MAG","ENC","BST","BER"
    };
    static bool Number(std::string_view text, uint32_t& result) {
        if (text.empty() || text.size() > 10) return false;
        uint32_t value = 0;
        for (char c : text) {
            if (c < '0' || c > '9') return false;
            const uint32_t digit = static_cast<uint32_t>(c - '0');
            if (value > (UINT32_MAX - digit) / 10) return false;
            value = value * 10 + digit;
        }
        result = value;
        return true;
    }
public:
    const std::array<uint32_t,5>& Identity() const { return identity_; }
    void Clear() { identity_ = {}; classes_ = {}; name_.clear(); aa_classes_.clear(); ClearRecommendations(); }
    bool RecommendationsReady() const { return recommendations_ready_; }
    size_t RecommendationCount() const { return recommended_.size(); }
    bool Recommended(uint32_t rank) const { return recommendations_ready_ && recommended_.count(rank); }
    std::string Recommendation(uint32_t rank) const {
        auto row = recommended_.find(rank);
        if (!recommendations_ready_ || row == recommended_.end()) return "";
        return std::string(row->second.status == 2 ? "Later: " : row->second.status == 1 ? "Needs prerequisite: " : "") +
            recommended_aa::Reason(row->second.reason) + " (aim: " + std::to_string(row->second.target) + ")";
    }
    uint32_t PrimaryClass() const { return classes_[0]; }
    uint32_t ClassMask() const {
        uint32_t mask = 0;
        for (auto id : classes_) if (id >= 1 && id <= 16) mask |= uint32_t(1) << (id - 1);
        return mask;
    }
    bool Matches(uint32_t spawn, const char* name) const {
        return identity_[0] && identity_[4] == spawn && name && name_ == name;
    }
    std::string Classes() const {
        return std::string(names_[classes_[0]]) + "/" + names_[classes_[1]] + "/" + names_[classes_[2]];
    }
    std::string AAClasses(uint32_t rank) const {
        auto found = aa_classes_.find(rank);
        if (found == aa_classes_.end()) return "Unknown";
        if (found->second == 0x1fffe) return "All";
        std::string result;
        for (unsigned id = 1; id <= 16; ++id) {
            if (!(found->second & (uint32_t(1) << id))) continue;
            if (!result.empty()) result += "/";
            result += names_[id];
        }
        return result.empty() ? "None" : result;
    }
    bool Consume(const char* message) {
        if (!message) return false;
        size_t size = 0;
        while (size < 256 && message[size]) ++size;
        if (size == 256) return false;
        const std::string_view text(message, size);
        if (text.size() < 10 || text.substr(0, 7) != "[NCUI1]" || text[8] != '|') return false;
        const char type = text[7];
        if (type != 'S' && type != 'A' && type != 'B' && type != 'R' && type != 'E') return false;
        std::array<std::string_view, 9> fields{};
        size_t count = 0, start = 9;
        while (start <= size) {
            if (count == fields.size()) return false;
            size_t end = text.find('|', start);
            if (end == std::string_view::npos) end = size;
            fields[count++] = text.substr(start, end - start);
            start = end + 1;
        }
        const size_t expected = type == 'S' || type == 'R' ? 9u : type == 'A' ? 7u : type == 'B' ? 6u : 5u;
        if (count != expected) return false;
        std::array<uint32_t, 9> values{};
        for (size_t i = 0; i < (type == 'S' ? 8u : expected); ++i) {
            if (!Number(fields[i], values[i])) return false;
        }
        if (!values[0] || !values[1] || !values[2] || !values[4] || values[4] > 65535) return false;
        std::array<uint32_t, 5> identity{};
        for (size_t i = 0; i < identity.size(); ++i) identity[i] = values[i];
        if (type == 'B' || type == 'R' || type == 'E') {
            if (identity != identity_) return false;
            if (type == 'B') {
                if (values[5]>10) return false;
                pending_recommended_.clear(); recommendations_expected_=values[5];
                recommendations_pending_=true; return true;
            }
            if (!recommendations_pending_) return false;
            if (type == 'R') {
                if (!values[5] || recommended_aa::Reason(values[6]).empty() || values[7] > 2 ||
                    !values[8] || values[8] > 255 || pending_recommended_.size() >= 10 || pending_recommended_.count(values[5])) return false;
                pending_recommended_[values[5]] = {values[6],values[7],values[8]};
            } else {
                recommendations_pending_=false;
                if (pending_recommended_.size()!=recommendations_expected_) { pending_recommended_.clear(); return false; }
                recommended_.swap(pending_recommended_); pending_recommended_.clear();
                recommendations_ready_ = true; recommendations_pending_ = false;
            }
            return true;
        }
        if (type == 'A') {
            if (identity != identity_ || !values[5] || (values[6] & ~uint32_t(0x1fffe))) return false;
            if (aa_classes_.size() >= 32768 && !aa_classes_.count(values[5])) return false;
            aa_classes_[values[5]] = values[6];
            return true;
        }
        if (!values[5] || values[5] > 16 || values[6] > 16 || values[7] > 16 ||
            values[5] == values[6] || values[5] == values[7] || (values[6] && values[6] == values[7])) return false;
        const auto name = fields[8];
        if (name.empty() || name.size() > 63) return false;
        for (char c : name) {
            if (!((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || c == '_')) return false;
        }
        if (identity_[1] == identity[1] && identity_[2] == identity[2] &&
            identity_[3] == identity[3] && identity_[4] == identity[4] && identity[0] <= identity_[0]) return false;
        identity_ = identity;
        classes_ = {values[5],values[6],values[7]};
        name_ = name;
        aa_classes_.clear();
        ClearRecommendations();
        return true;
    }
};
}
