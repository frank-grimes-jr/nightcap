#include <windows.h>
#include <cstdio>
extern "C" __declspec(dllexport) DWORD WINAPI InitializeFixture(void*) {
    wchar_t mode[20];
    GetEnvironmentVariableW(L"NIGHTCAP_BOOTSTRAP_TEST",mode,20);
    if(wcscmp(mode,L"hang")==0) {Sleep(60000);return 2;}
    if(wcscmp(mode,L"fail")==0)return 3;
    if(wcscmp(mode,L"crash")==0) {RaiseException(0xE0000001,EXCEPTION_NONCONTINUABLE,0,nullptr);return 4;}
    // Exercises DLL CRT and loader activity, not just a bare machine-code stub.
    FILE* file=nullptr;
    if(fopen_s(&file,"bootstrap-ready","wx") || !file)return 5;
    fputs("ready",file);
    if(fclose(file))return 6;
    HMODULE version=LoadLibraryW(L"version.dll");
    if(!version)return 7;
    FreeLibrary(version);
    return 0;
}
BOOL WINAPI DllMain(HINSTANCE,DWORD,LPVOID){return TRUE;}
