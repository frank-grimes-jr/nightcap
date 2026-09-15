#include <windows.h>
extern "C" __declspec(dllimport) DWORD WINAPI NightcapInitialize(void*);
int main(int argc,char**) {
    if(argc==777)NightcapInitialize(nullptr); // retain the proxy import
    HANDLE file=CreateFileW(L"main-entered",GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(file==INVALID_HANDLE_VALUE)return 2;
    CloseHandle(file);return 0;
}
