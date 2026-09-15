#include <windows.h>
#include <cstdio>
#include <cstring>
int wmain(int argc,wchar_t** argv) {
    if(argc<2)return 3;
    // The test copies this executable and the candidate into one disposable
    // directory; the real game executable/client is never launched or modified.
    HMODULE module=LoadLibraryW(argv[1]);
    if(!module){printf("load failed %lu\n",GetLastError());return 4;}
    if(argc>2 && wcscmp(argv[2],L"unload")==0) {
        auto unload=reinterpret_cast<HRESULT (WINAPI*)()>(GetProcAddress(module,"DllCanUnloadNow"));
        if(!unload || unload()!=S_FALSE)return 6;
        return FreeLibrary(module) ? 0 : 7;
    }
    auto call=reinterpret_cast<const void* (WINAPI*)()>(GetProcAddress(module,"GetdfDIJoystick"));
    if(!call)return 5;
    call();
    puts("ERROR: unsupported host returned through the startup gate");
    return 9;
}
