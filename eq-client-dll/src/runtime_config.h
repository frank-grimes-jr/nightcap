#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>
#include "runtime_contract.h"

namespace nightcap {
struct RuntimeConfig {
    uint32_t enabled_mask = 0;
    bool mq2_survey = false;
};
// Matches the Go configuration contract: exact ASCII keys, 0/1 values, no
// ignored defaults, duplicate keys, comments or BOM. LF and CRLF are accepted.
inline bool ParseRuntimeConfig(const char* data, size_t size, RuntimeConfig& out, const char*& reason) {
    out = RuntimeConfig{};
    reason = "invalid_configuration";
    if (!data || size == 0 || size > 4096) return false;
    bool schema_seen = false, survey_seen = false;
    uint32_t seen = 0;
    size_t begin = 0;
    while (begin < size) {
        size_t end = begin;
        while (end < size && data[end] != '\n') ++end;
        size_t length = end - begin;
        if (end < size && length && data[begin + length - 1] == '\r') --length;
        const char* line = data + begin;
        if (length < 3 || line[length - 2] != '=' || (line[length - 1] != '0' && line[length - 1] != '1')) return false;
        const size_t key_length = length - 2;
        const bool enabled = line[length - 1] == '1';
        bool known = false;
        if (key_length == 6 && memcmp(line, "schema", 6) == 0) {
            if (schema_seen || !enabled) return false;
            schema_seen = known = true;
        } else if (key_length == 10 && memcmp(line, "mq2_survey", 10) == 0) {
            if (survey_seen) return false;
            out.mq2_survey = enabled;
            survey_seen = known = true;
        } else {
            for (size_t i = 0; i < kRequiredFeatureCount; ++i) {
                if (strlen(kRequiredFeatures[i]) != key_length || memcmp(line, kRequiredFeatures[i], key_length) != 0) continue;
                const uint32_t bit = uint32_t(1) << i;
                if (seen & bit) return false;
                seen |= bit;
                if (!enabled) { reason = kRequiredFeatures[i]; return false; }
                out.enabled_mask |= bit;
                known = true;
                break;
            }
        }
        if (!known) return false;
        begin = end + (end < size ? 1 : 0);
    }
    if (!schema_seen || !survey_seen || seen != kRequiredMask) {reason = "missing_configuration"; return false;}
    reason = "";
    return true;
}
inline bool IsLowerHex(const char* value, size_t size) {
    for (size_t i = 0; i < size; ++i) {
        const char c = value[i];
        if (!(c >= '0' && c <= '9') && !(c >= 'a' && c <= 'f')) return false;
    }
    return true;
}
}
