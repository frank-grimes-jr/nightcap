#include "../src/runtime_health.h"
#include <cassert>
#include <cstdio>
#pragma comment(lib,"bcrypt.lib")
int wmain(int argc,wchar_t** argv) {
    if(argc!=2)return 3;
    nightcap::RuntimeHealth health;
    health.pid=GetCurrentProcessId();
    health.process_created=123456789;
    strcpy_s(health.nonce,"0123456789abcdef0123456789abcdef");
    assert(nightcap::DigestBytes(reinterpret_cast<const BYTE*>("fixture"),7,health.config_sha256));
    health.enabled_mask=health.applied_mask=nightcap::kRequiredMask;
    char bytes[2048];
    assert(nightcap::FormatHealth(health,"ready","",bytes));
    assert(!nightcap::FormatHealth(health,"bad","",bytes));
    assert(!nightcap::FormatHealth(health,"ready","bad\"reason",bytes));
    wchar_t temporary[MAX_PATH], target[MAX_PATH];
    assert(swprintf_s(temporary,L"%snightcap_health_%lu_%llu.tmp",argv[1],health.pid,health.process_created)>0);
    assert(swprintf_s(target,L"%snightcap_health_%lu.json",argv[1],health.pid)>0);
    HANDLE occupied=CreateFileW(temporary,GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    assert(occupied!=INVALID_HANDLE_VALUE);
    assert(!nightcap::WriteHealth(argv[1],health,"ready",""));
    assert(CloseHandle(occupied));
    assert(GetFileAttributesW(temporary)!=INVALID_FILE_ATTRIBUTES);
    assert(DeleteFileW(temporary));
    assert(CreateDirectoryW(target,nullptr));
    assert(!nightcap::WriteHealth(argv[1],health,"ready",""));
    assert(GetFileAttributesW(temporary)==INVALID_FILE_ATTRIBUTES);
    assert(GetFileAttributesW(target)&FILE_ATTRIBUTE_DIRECTORY);
    assert(RemoveDirectoryW(target));
    assert(nightcap::WriteHealth(argv[1],health,"initializing",""));
    assert(nightcap::WriteHealth(argv[1],health,"ready",""));
    assert(nightcap::FormatHealth(health,"ready","",bytes));
    puts(bytes);
    return 0;
}
