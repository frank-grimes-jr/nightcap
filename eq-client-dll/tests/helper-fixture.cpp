#include <windows.h>
#include <cwchar>
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
    return CloseHandle(file)&&okay?0:7;
}
BOOL WINAPI DllMain(HINSTANCE,DWORD,LPVOID){return TRUE;}
