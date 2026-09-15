#include <windows.h>
#include <cwchar>
#include "../src/runtime_health.h"
extern "C" DWORD WINAPI NightcapInitialize(void*) {
    wchar_t mode[20]={},nonce[34]={};
    GetEnvironmentVariableW(L"NIGHTCAP_BOOTSTRAP_TEST",mode,20);
    if(wcscmp(mode,L"hang")==0){Sleep(60000);return 2;}
    if(wcscmp(mode,L"fail")==0)return 3;
    if(wcscmp(mode,L"crash")==0){RaiseException(0xe0000001,EXCEPTION_NONCONTINUABLE,0,nullptr);return 4;}
    if(GetEnvironmentVariableW(L"NIGHTCAP_LAUNCH_NONCE",nonce,34)!=32)return 5;
    HANDLE file=CreateFileW(L"bootstrap-ready",GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(file==INVALID_HANDLE_VALUE)return 6;
    DWORD written=0;
    bool okay=WriteFile(file,nonce,64,&written,nullptr)&&written==64;
    if(!CloseHandle(file)||!okay)return 7;
    if(wcscmp(mode,L"missing_health")==0)return 0;
    nightcap::RuntimeHealth health;
    health.pid=GetCurrentProcessId();
    FILETIME created,exited,kernel,user;
    if(!GetProcessTimes(GetCurrentProcess(),&created,&exited,&kernel,&user))return 8;
    health.process_created=(static_cast<unsigned long long>(created.dwHighDateTime)<<32)|created.dwLowDateTime;
    for(unsigned i=0;i<32;++i)health.nonce[i]=static_cast<char>(nonce[i]);
    health.enabled_mask=health.applied_mask=nightcap::kRequiredMask;
    HANDLE config=CreateFileW(L"nightcap-patches.cfg",GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,0,nullptr);
    if(config==INVALID_HANDLE_VALUE)return 9;
    BYTE data[4097]={};DWORD size=0;
    okay=ReadFile(config,data,sizeof(data),&size,nullptr)&&size>0&&size<=4096;
    if(!CloseHandle(config)||!okay||!nightcap::DigestBytes(data,size,health.config_sha256))return 10;
    if(wcscmp(mode,L"bad_nonce")==0)health.nonce[0]=health.nonce[0]=='0'?'1':'0';
    if(wcscmp(mode,L"bad_mask")==0)health.applied_mask=0;
    if(wcscmp(mode,L"bad_config")==0)health.config_sha256[0]=health.config_sha256[0]=='0'?'1':'0';
    if(wcscmp(mode,L"bad_created")==0)++health.process_created;
    wchar_t directory[MAX_PATH]={};
    DWORD length=GetCurrentDirectoryW(MAX_PATH,directory);
    if(!length||length>=MAX_PATH-1)return 11;
    directory[length]=L'\\';directory[length+1]=0;
    bool failed=wcscmp(mode,L"failed_health")==0;
    return nightcap::WriteHealth(directory,health,failed?"failed":"ready",failed?"fixture_failure":"")?0:12;
}
BOOL WINAPI DllMain(HINSTANCE,DWORD,LPVOID){return TRUE;}
