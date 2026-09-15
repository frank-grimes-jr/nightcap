#pragma once
#include <windows.h>
#include <cstdint>
#include <algorithm>
#include <cstring>

namespace nightcap {
// Little-endian, fixed-width local pipe protocol. No pointers, JSON, shell
// commands or UI-provided process IDs. Handles are explicit inherited duplicates.
constexpr uint32_t kBootstrapMagic=0x4e434231;
struct BootstrapRequest {
    uint32_t magic,version;
    uint64_t executable_file,proxy_file,parent_process;
    uint32_t entry_rva,initializer_rva,proxy_image_size,timeout_ms,entry_original,directory_units;
};
static_assert(sizeof(BootstrapRequest)==56,"bootstrap wire request layout");
enum BootstrapMessageKind : uint32_t { Failure=0,HealthRequired=1,Started=2,Exited=3 };
struct BootstrapMessage {
    uint32_t magic,kind,pid,code;
    uint64_t created;
    char reason[64];
};
static_assert(sizeof(BootstrapMessage)==88,"bootstrap wire response layout");

inline bool ReadPipeUntil(HANDLE pipe,void* data,DWORD size,ULONGLONG deadline) {
    auto target=static_cast<BYTE*>(data);
    while(size && GetTickCount64()<deadline) {
        DWORD available=0,read=0;
        if(!PeekNamedPipe(pipe,nullptr,0,nullptr,&available,nullptr))return false;
        if(!available){Sleep(10);continue;}
        DWORD take=(std::min)(available,size);
        if(!ReadFile(pipe,target,take,&read,nullptr)||!read)return false;
        target+=read;size-=read;
    }
    return size==0;
}
inline bool WriteBootstrapMessage(HANDLE pipe,BootstrapMessageKind kind,DWORD pid,
        uint64_t created,DWORD code,const char* reason) {
    BootstrapMessage message={kBootstrapMagic,kind,pid,code,created,{}};
    if(reason && strncpy_s(message.reason,reason,_TRUNCATE)!=0)return false;
    DWORD written=0;
    // At most three 88-byte responses are outstanding. The launcher's anonymous
    // output pipe must have at least 4096 bytes of capacity, and a dedicated reader.
    return WriteFile(pipe,&message,sizeof(message),&written,nullptr) && written==sizeof(message);
}
}
