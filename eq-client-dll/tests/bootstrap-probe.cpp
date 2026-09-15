// Only creates another instance of this fixture, never eqgame.
#include "../bootstrap/entry_gate.h"
#include <cstdio>
#include <cwchar>
#include <type_traits>
static_assert(!std::is_copy_constructible<nightcap::EntryGateResult>::value,"session owns unique handles");
extern "C" __declspec(dllimport) DWORD WINAPI InitializeFixture(void*);
static bool Marker(const wchar_t* name) {
    HANDLE file=CreateFileW(name,GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    return file!=INVALID_HANDLE_VALUE && CloseHandle(file);
}
static bool Verify(HANDLE, const nightcap::EntryGateResult& result, ULONGLONG, void*) {
    wchar_t mode[20]={};GetEnvironmentVariableW(L"NIGHTCAP_BOOTSTRAP_TEST",mode,20);
    if(wcscmp(mode,L"owner_crash")==0) {
        FILE* file=nullptr;
        if(fopen_s(&file,"owner-child","w")||!file)return false;
        fprintf(file,"%lu %llu",result.pid,result.created);fclose(file);
        TerminateProcess(GetCurrentProcess(),77);__fastfail(7);
    }
    if(wcscmp(mode,L"reject")==0)return false;
    return result.created!=0 && Marker(L"verified-before-main") &&
        GetFileAttributesW(L"bootstrap-ready")!=INVALID_FILE_ATTRIBUTES &&
        GetFileAttributesW(L"main-entered")==INVALID_FILE_ATTRIBUTES;
}
int wmain(int argc,wchar_t** argv) {
    if(argc==2 && wcscmp(argv[1],L"child")==0) {
        if(GetFileAttributesW(L"impossible-force-import")!=INVALID_FILE_ATTRIBUTES)InitializeFixture(nullptr);
        return Marker(L"main-entered") ? 0 : 20;
    }
    wchar_t executable[MAX_PATH],command[MAX_PATH+16],directory[MAX_PATH],mode[20]={};
    DWORD n=GetModuleFileNameW(nullptr,executable,MAX_PATH);
    if(!n||n>=MAX_PATH||swprintf_s(command,L"\"%s\" child",executable)<0)return 2;
    n=GetCurrentDirectoryW(MAX_PATH,directory);if(!n||n>=MAX_PATH)return 3;
    GetEnvironmentVariableW(L"NIGHTCAP_BOOTSTRAP_TEST",mode,20);
    bool candidate=wcscmp(mode,L"candidate")==0;
    if(candidate) {
        wchar_t* separator=wcsrchr(executable,L'\\');if(!separator)return 4;
        *(separator+1)=0;if(wcscat_s(executable,L"bootstrap-host.exe"))return 4;
        if(swprintf_s(command,L"\"%s\"",executable)<0)return 4;
    }
    HANDLE exe=CreateFileW(executable,GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,0,nullptr);
    HANDLE dll=CreateFileW(candidate?L"dinput8.dll":L"bootstrap-fixture.dll",GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,0,nullptr);
    if(exe==INVALID_HANDLE_VALUE||dll==INVALID_HANDLE_VALUE)return 4;
    HMODULE mapped_exe=candidate?LoadLibraryExW(executable,nullptr,DONT_RESOLVE_DLL_REFERENCES):nullptr;
    if(candidate&&!mapped_exe)return 4;
    auto local_image=reinterpret_cast<BYTE*>(candidate?mapped_exe:GetModuleHandleW(nullptr));
    auto nt=reinterpret_cast<IMAGE_NT_HEADERS*>(local_image+reinterpret_cast<IMAGE_DOS_HEADER*>(local_image)->e_lfanew);
    HMODULE local=candidate?LoadLibraryExW(L"dinput8.dll",nullptr,DONT_RESOLVE_DLL_REFERENCES):GetModuleHandleW(L"bootstrap-fixture.dll");
    if(!local)return 5;
    auto proxy_image=reinterpret_cast<BYTE*>(local);
    auto proxy_nt=reinterpret_cast<IMAGE_NT_HEADERS*>(proxy_image+reinterpret_cast<IMAGE_DOS_HEADER*>(proxy_image)->e_lfanew);
    auto init=GetProcAddress(local,candidate?"NightcapInitialize":"InitializeFixture");if(!init)return 5;
    nightcap::EntryGateInputs input={executable,command,directory,nullptr,exe,dll,
        nt->OptionalHeader.AddressOfEntryPoint,local_image[nt->OptionalHeader.AddressOfEntryPoint],
        static_cast<uint32_t>(reinterpret_cast<uintptr_t>(init)-reinterpret_cast<uintptr_t>(local)),
        proxy_nt->OptionalHeader.SizeOfImage,3000};
    if(wcscmp(mode,L"wrong_entry")==0)input.entry_rva+=1;
    if(wcscmp(mode,L"wrong_byte")==0)input.entry_original^=1;
    if(wcscmp(mode,L"wrong_proxy")==0)input.proxy_file=exe;
    bool all_ok=true;
    unsigned repeats=wcscmp(mode,L"repeat")==0?5:1;
    for(unsigned run=0;run<repeats;++run) {
        if(run) {
            DeleteFileW(L"main-entered");DeleteFileW(L"bootstrap-ready");DeleteFileW(L"verified-before-main");
            if(swprintf_s(command,L"\"%s\" child",executable)<0)return 6;
        }
    DWORD handles_before=0,handles_after=0;
    GetProcessHandleCount(GetCurrentProcess(),&handles_before);
    auto result=nightcap::RunEntryGate(input,Verify,nullptr);

    // The successful fixture runs independently after the gate resumes it.
    const ULONGLONG deadline=GetTickCount64()+3000;
    while(result.started && GetFileAttributesW(L"main-entered")==INVALID_FILE_ATTRIBUTES && GetTickCount64()<deadline)Sleep(10);
    if(result.started) {
        if(WaitForSingleObject(result.process,3000)!=WAIT_OBJECT_0) {
            CloseHandle(result.job);result.job=nullptr;
            WaitForSingleObject(result.process,3000);
            result.started=false;
        }
        result.Close();
    }
    GetProcessHandleCount(GetCurrentProcess(),&handles_after);
    printf("handles_before=%lu after=%lu\n",handles_before,handles_after);
    bool main=GetFileAttributesW(L"main-entered")!=INVALID_FILE_ATTRIBUTES;
    printf("started=%u pid=%lu created=%llu init_exit=%lu main=%u reason=%s\n",
        result.started,result.pid,result.created,result.initializer_exit,main,result.failure);
        all_ok=all_ok && result.started && main;
        if(run && handles_after>handles_before)all_ok=false;
    }
    CloseHandle(exe);CloseHandle(dll);
    if(candidate){FreeLibrary(local);FreeLibrary(mapped_exe);}
    return all_ok ? 0 : 1;
}
