#include <windows.h>
extern "C" __declspec(dllimport) DWORD WINAPI NightcapInitialize(void*);
int main(int argc,char**) {
    if(argc==777)NightcapInitialize(nullptr);
    HANDLE file=CreateFileW(L"main-entered",GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(file==INVALID_HANDLE_VALUE)return 2;
    CloseHandle(file);
    wchar_t hold[2]={};
    if(GetEnvironmentVariableW(L"NIGHTCAP_HELPER_HOLD",hold,2)==1 && hold[0]==L'1')Sleep(60000);
    return 0;
}
