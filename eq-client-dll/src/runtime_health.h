#pragma once
#include <windows.h>
#include <bcrypt.h>
#include <cstdio>
#include <cstring>
#include "runtime_config.h"

namespace nightcap {
struct RuntimeHealth {
    DWORD pid = 0;
    unsigned long long process_created = 0;
    char nonce[33] = {};
    char config_sha256[65] = {};
    uint32_t enabled_mask = 0;
    uint32_t applied_mask = 0;
    bool mq2_survey = false;
};
inline bool DigestBytes(const BYTE* data, DWORD size, char (&hex)[65]) {
    BCRYPT_ALG_HANDLE algorithm = nullptr;
    BYTE digest[32] = {};
    if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0) return false;
    const NTSTATUS result = BCryptHash(algorithm, nullptr, 0, const_cast<BYTE*>(data), size, digest, sizeof(digest));
    BCryptCloseAlgorithmProvider(algorithm, 0);
    if (result < 0) return false;
    for (size_t i = 0; i < 32; ++i) sprintf_s(hex + i * 2, 65 - i * 2, "%02x", digest[i]);
    return true;
}
inline bool SafeReason(const char* reason) {
    if (!reason || strlen(reason) > 64) return false;
    for (const char* p = reason; *p; ++p) if (!(*p >= 'a' && *p <= 'z') && !(*p >= '0' && *p <= '9') && *p != '_') return false;
    return true;
}
inline bool FormatHealth(const RuntimeHealth& health, const char* state, const char* reason, char (&out)[2048]) {
    if ((!state || (strcmp(state,"ready") && strcmp(state,"failed") && strcmp(state,"initializing"))) || !SafeReason(reason)) return false;
    const size_t nonce_size = strlen(health.nonce);
    if ((nonce_size != 0 && nonce_size != 32) || !IsLowerHex(health.nonce,nonce_size)) return false;
    const size_t hash_size = strlen(health.config_sha256);
    if ((hash_size != 0 && hash_size != 64) || !IsLowerHex(health.config_sha256,hash_size)) return false;
    return sprintf_s(out,
        "{\"schema\":%u,\"proxy_version\":\"%s\",\"catalog_sha256\":\"%s\",\"config_sha256\":\"%s\","
        "\"pid\":%lu,\"process_created\":\"%llu\",\"nonce\":\"%s\",\"state\":\"%s\","
        "\"required_mask\":%u,\"enabled_mask\":%u,\"applied_mask\":%u,\"mq2_survey\":%s,\"reason\":\"%s\"}",
        kRuntimeSchema,kProxyVersion,kCatalogSHA256,health.config_sha256,health.pid,health.process_created,health.nonce,state,
        kRequiredMask,health.enabled_mask,health.applied_mask,health.mq2_survey?"true":"false",reason) > 0;
}
// New private temporary; replacing the final name never truncates it in place.
// An occupied temporary or failed flush/rename fails rather than following it.
inline bool WriteHealth(const wchar_t* directory, const RuntimeHealth& health, const char* state, const char* reason) {
    if (!directory || !*directory) return false;
    wchar_t target[MAX_PATH], temporary[MAX_PATH];
    if (swprintf_s(target,L"%snightcap_health_%lu.json",directory,health.pid) < 0 ||
        swprintf_s(temporary,L"%snightcap_health_%lu_%llu.tmp",directory,health.pid,health.process_created) < 0) return false;
    char bytes[2048];
    if (!FormatHealth(health,state,reason,bytes)) return false;
    HANDLE file = CreateFileW(temporary,GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL|FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
    if (file == INVALID_HANDLE_VALUE) return false;
    const DWORD size = static_cast<DWORD>(strlen(bytes));
    DWORD written = 0;
    bool okay = WriteFile(file,bytes,size,&written,nullptr) && written == size && FlushFileBuffers(file);
    if (!CloseHandle(file)) okay = false;
    if (okay) okay = MoveFileExW(temporary,target,MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH) != FALSE;
    if (!okay) DeleteFileW(temporary);
    return okay;
}
}
