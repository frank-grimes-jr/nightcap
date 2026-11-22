#pragma once
#include <windows.h>
#include <cstdint>
#include <cstring>
#include <string>
#pragma comment(lib, "advapi32.lib")

namespace nightcap::item_notes {
constexpr size_t Limit = 240;
inline constexpr char UserKey[] = "Software\\Nightcap\\ItemNotes";

inline bool Valid(const std::string& text) {
    if (text.size() > Limit) return false;
    for (unsigned char c : text) if (c < 32 || c == 127) return false;
    return true;
}

// Each item owns one atomic REG_SZ value. The ANSI registry functions store
// Unicode and convert through the same Windows code page as the RoF2 client.
class Store {
    const char* key_;
public:
    explicit Store(const char* key = UserKey) : key_(key) {}
    bool Read(uint32_t id, std::string& result) const {
        if (!id) return false;
        char value[Limit + 2]{};
        DWORD bytes = sizeof(value);
        const auto name = std::to_string(id);
        const auto error = RegGetValueA(HKEY_CURRENT_USER, key_, name.c_str(), RRF_RT_REG_SZ,
                                        nullptr, value, &bytes);
        if (error == ERROR_FILE_NOT_FOUND || error == ERROR_PATH_NOT_FOUND) {
            result.clear();
            return true;
        }
        if (error != ERROR_SUCCESS || !bytes || bytes > Limit + 1 || strlen(value) != bytes - 1) return false;
        std::string text(value, bytes - 1);
        if (!Valid(text)) return false;
        result = text;
        return true;
    }
    bool Save(uint32_t id, const std::string& text) const {
        if (!id || !Valid(text)) return false;
        const auto name = std::to_string(id);
        if (text.empty()) {
            const auto error = RegDeleteKeyValueA(HKEY_CURRENT_USER, key_, name.c_str());
            return error == ERROR_SUCCESS || error == ERROR_FILE_NOT_FOUND || error == ERROR_PATH_NOT_FOUND;
        }
        return RegSetKeyValueA(HKEY_CURRENT_USER, key_, name.c_str(), REG_SZ, text.c_str(),
                               static_cast<DWORD>(text.size() + 1)) == ERROR_SUCCESS;
    }
};
}
