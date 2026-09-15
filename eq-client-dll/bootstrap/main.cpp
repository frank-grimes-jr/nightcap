#include "entry_gate.h"
#include "protocol.h"
#include <string>
#include <vector>

namespace {
struct ParentWatch {
    HANDLE parent=nullptr,stop=nullptr,thread=nullptr,input=nullptr;
    volatile LONG session_started=0;
    static DWORD WINAPI Run(void* opaque) {
        auto self=static_cast<ParentWatch*>(opaque);
        HANDLE wait[]={self->parent,self->stop};
        for(;;) {
            DWORD state=WaitForMultipleObjects(2,wait,FALSE,50);
            if(state==WAIT_OBJECT_0+1)break;
            if(state==WAIT_TIMEOUT) {
                if(!InterlockedCompareExchange(&self->session_started,0,0))continue;
                DWORD available=0;
                if(PeekNamedPipe(self->input,nullptr,0,nullptr,&available,nullptr))continue;
            }
            // Parent death or a closed session channel terminates this helper.
            // Debugger exit / the retained job contains only its owned child.
            TerminateProcess(GetCurrentProcess(),0x4e430003);__fastfail(7);
        }
        return 0;
    }
    bool Start(HANDLE handle,HANDLE pipe) {
        parent=handle;input=pipe;
        if(!GetProcessId(parent)||GetProcessId(parent)==GetCurrentProcessId()||
           WaitForSingleObject(parent,0)!=WAIT_TIMEOUT)return false;
        stop=CreateEventW(nullptr,TRUE,FALSE,nullptr);
        if(!stop)return false;
        thread=CreateThread(nullptr,0,Run,this,0,nullptr);
        return thread!=nullptr;
    }
    ~ParentWatch() {
        if(thread){
            if(!SetEvent(stop)||WaitForSingleObject(thread,5000)!=WAIT_OBJECT_0)
                nightcap::AbortBootstrap("parent_watch_stop");
            CloseHandle(thread);
        }
        if(stop)CloseHandle(stop);
        if(parent)CloseHandle(parent);
    }
};
struct HealthChannel {HANDLE input,output;};
bool ApproveHealth(HANDLE,const nightcap::EntryGateResult& result,ULONGLONG deadline,void* opaque) {
    auto channel=static_cast<HealthChannel*>(opaque);
    if(!nightcap::WriteBootstrapMessage(channel->output,nightcap::HealthRequired,result.pid,result.created,0,""))return false;
    uint32_t approval=0;
    return nightcap::ReadPipeUntil(channel->input,&approval,sizeof(approval),deadline) && approval==1;
}
HANDLE InheritedHandle(uint64_t value) {
    if(!value||value>UINT32_MAX)return nullptr;
    HANDLE handle=reinterpret_cast<HANDLE>(static_cast<uintptr_t>(value));
    DWORD flags=0;
    return GetHandleInformation(handle,&flags)?handle:nullptr;
}
void CloseSession(nightcap::EntryGateResult& result) {
    if(result.job){CloseHandle(result.job);result.job=nullptr;}
    if(result.process && WaitForSingleObject(result.process,5000)!=WAIT_OBJECT_0)
        nightcap::AbortBootstrap("session_exit");
    result.Close();
}
int Fail(HANDLE output,const char* reason) {
    nightcap::WriteBootstrapMessage(output,nightcap::Failure,0,0,1,reason);
    return 1;
}
}
int wmain(int argc,wchar_t**) {
    HANDLE input=GetStdHandle(STD_INPUT_HANDLE),output=GetStdHandle(STD_OUTPUT_HANDLE);
    if(argc!=1||GetFileType(input)!=FILE_TYPE_PIPE||GetFileType(output)!=FILE_TYPE_PIPE)return 2;
    nightcap::BootstrapRequest request={};
    const ULONGLONG deadline=GetTickCount64()+5000;
    if(!nightcap::ReadPipeUntil(input,&request,sizeof(request),deadline))return Fail(output,"request_read");
    if(request.magic!=nightcap::kBootstrapMagic||request.version!=1||!request.directory_units||
       request.directory_units>32700||!request.timeout_ms||request.timeout_ms>60000||
       request.entry_original>255||request.entry_original==0xcc)return Fail(output,"request_invalid");
    HANDLE exe=InheritedHandle(request.executable_file),proxy=InheritedHandle(request.proxy_file),parent=InheritedHandle(request.parent_process);
    if(!exe||!proxy||!parent||GetFileType(exe)!=FILE_TYPE_DISK||GetFileType(proxy)!=FILE_TYPE_DISK)return Fail(output,"request_handles");
    ParentWatch watch;
    if(!watch.Start(parent,input))return Fail(output,"parent_watch");
    std::vector<wchar_t> directory(request.directory_units+1,0);
    if(!nightcap::ReadPipeUntil(input,directory.data(),request.directory_units*2,deadline))return Fail(output,"directory_read");
    for(uint32_t i=0;i<request.directory_units;++i)
        if(!directory[i]||directory[i]==L'"'||directory[i]<32)return Fail(output,"directory_invalid");
    if(request.directory_units<3||directory[1]!=L':'||directory[2]!=L'\\')return Fail(output,"directory_invalid");
    wchar_t nonce[34]={};
    if(GetEnvironmentVariableW(L"NIGHTCAP_LAUNCH_NONCE",nonce,34)!=32)return Fail(output,"nonce_invalid");
    for(unsigned i=0;i<32;++i)if(!((nonce[i]>=L'0'&&nonce[i]<=L'9')||(nonce[i]>=L'a'&&nonce[i]<=L'f')))return Fail(output,"nonce_invalid");
    std::wstring executable=std::wstring(directory.data())+L"\\eqgame.exe";
    std::wstring command=L"\""+executable+L"\" patchme";
    // The launcher gives this helper a private environment. Snapshot it for the
    // child; never change the launcher/global environment to set the nonce.
    LPWCH environment=GetEnvironmentStringsW();
    if(!environment)return Fail(output,"environment");
    nightcap::EntryGateInputs gate={executable.c_str(),&command[0],directory.data(),environment,
        exe,proxy,request.entry_rva,static_cast<BYTE>(request.entry_original),request.initializer_rva,
        request.proxy_image_size,request.timeout_ms};
    HealthChannel channel={input,output};
    auto result=nightcap::RunEntryGate(gate,ApproveHealth,&channel);
    FreeEnvironmentStringsW(environment);
    if(!result.started) {
        nightcap::WriteBootstrapMessage(output,nightcap::Failure,result.pid,result.created,result.initializer_exit,result.failure);
        return 3;
    }
    InterlockedExchange(&watch.session_started,1);
    if(!nightcap::WriteBootstrapMessage(output,nightcap::Started,result.pid,result.created,0,"")) {
        CloseSession(result);return 4;
    }
    // The helper remains the session's process/job owner. Parent loss closes the
    // job via process exit; cancellation kills this helper, never an arbitrary PID.
    if(WaitForSingleObject(result.process,INFINITE)!=WAIT_OBJECT_0)nightcap::AbortBootstrap("session_wait");
    DWORD code=0;
    if(!GetExitCodeProcess(result.process,&code))nightcap::AbortBootstrap("session_status");
    bool reported=nightcap::WriteBootstrapMessage(output,nightcap::Exited,result.pid,result.created,code,"");
    CloseSession(result);
    return reported?0:5;
}
