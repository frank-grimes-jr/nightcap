#pragma once
#include <windows.h>
#include <cstdint>
#include <intrin.h>
#include <cstdio>

namespace nightcap {
// x86 bootstrap primitive, called on a dedicated bootstrap process/thread.
// Inputs come from verified, read-locked PE files; RVAs are not user/UI input.
// This creates only a new owned process, never attaches to an existing PID.
struct EntryGateInputs {
    const wchar_t* executable;
    wchar_t* command_line;
    const wchar_t* directory;
    void* environment; // private double-NUL Unicode block, or inherited for tests
    HANDLE executable_file;
    HANDLE proxy_file;
    uint32_t entry_rva;
    BYTE entry_original;
    uint32_t initializer_rva;
    uint32_t proxy_image_size;
    DWORD timeout_ms;
};
struct EntryGateResult {
    // On success, caller owns both handles and must retain containment until
    // process exit or transfer to its session owner. Closing job kills the child.
    HANDLE process = nullptr;
    HANDLE job = nullptr;
    bool started = false;
    DWORD pid = 0;
    unsigned long long created = 0;
    DWORD initializer_exit = STILL_ACTIVE;
    const char* failure = "invalid_inputs";
    EntryGateResult() = default;
    EntryGateResult(const EntryGateResult&) = delete;
    EntryGateResult& operator=(const EntryGateResult&) = delete;
    EntryGateResult(EntryGateResult&& other) noexcept : process(other.process),job(other.job),
        started(other.started),pid(other.pid),created(other.created),
        initializer_exit(other.initializer_exit),failure(other.failure) {
        other.process=nullptr;other.job=nullptr;
    }
    EntryGateResult& operator=(EntryGateResult&&) = delete;
    void Close() {
        if(job){CloseHandle(job);job=nullptr;}
        if(process){CloseHandle(process);process=nullptr;}
    }
    ~EntryGateResult(){Close();}
};
// Runs while the primary thread remains suspended. Must be bounded by deadline
// and validate the actual process-bound health before returning true.
using VerifyEntryHealth = bool (*)(HANDLE, const EntryGateResult&, ULONGLONG deadline, void*);

__declspec(noreturn) inline void AbortBootstrap(const char* reason) {
    // Dedicated bootstrap process only. Never return to code that could resume
    // a child whose termination could not be confirmed. Windows kills attached
    // debuggees on debugger exit; kill-on-close jobs cover detached children.
    fprintf(stderr,"bootstrap cleanup failure: %s error=%lu\n",reason,GetLastError());
    TerminateProcess(GetCurrentProcess(),0x4E43FFFF);
    __fastfail(7);
}
inline bool SameFileIdentity(HANDLE a, HANDLE b) {
    BY_HANDLE_FILE_INFORMATION x={},y={};
    return a && b && GetFileInformationByHandle(a,&x) && GetFileInformationByHandle(b,&y) &&
        x.dwVolumeSerialNumber==y.dwVolumeSerialNumber &&
        x.nFileIndexHigh==y.nFileIndexHigh && x.nFileIndexLow==y.nFileIndexLow;
}
inline void CloseDebugFile(const DEBUG_EVENT& event) {
    if(event.dwDebugEventCode==CREATE_PROCESS_DEBUG_EVENT && event.u.CreateProcessInfo.hFile)
        CloseHandle(event.u.CreateProcessInfo.hFile);
    if(event.dwDebugEventCode==LOAD_DLL_DEBUG_EVENT && event.u.LoadDll.hFile)
        CloseHandle(event.u.LoadDll.hFile);
    // Debug-event process/thread handles are OS-owned until their exit event;
    // CreateProcess/CreateRemoteThread handles below are independently owned.
}
inline bool MatchesRemoteEntry(HANDLE process, uintptr_t base, uint32_t entry_rva) {
    IMAGE_DOS_HEADER dos={};IMAGE_NT_HEADERS32 nt={};SIZE_T count=0;
    if(!ReadProcessMemory(process,reinterpret_cast<void*>(base),&dos,sizeof(dos),&count)||count!=sizeof(dos)||
       dos.e_magic!=IMAGE_DOS_SIGNATURE||dos.e_lfanew<static_cast<LONG>(sizeof(dos))||dos.e_lfanew>0x100000||
       base>UINTPTR_MAX-static_cast<uint32_t>(dos.e_lfanew))return false;
    if(!ReadProcessMemory(process,reinterpret_cast<void*>(base+dos.e_lfanew),&nt,sizeof(nt),&count)||count!=sizeof(nt))return false;
    return nt.Signature==IMAGE_NT_SIGNATURE && nt.FileHeader.Machine==IMAGE_FILE_MACHINE_I386 &&
        nt.OptionalHeader.Magic==IMAGE_NT_OPTIONAL_HDR32_MAGIC &&
        nt.OptionalHeader.AddressOfEntryPoint==entry_rva && entry_rva<nt.OptionalHeader.SizeOfImage;
}
inline bool ReplaceRemoteByte(HANDLE process, void* site, BYTE expected, BYTE replacement) {
    BYTE actual=0;SIZE_T count=0;
    if(!ReadProcessMemory(process,site,&actual,1,&count)||count!=1||actual!=expected)return false;
    DWORD previous=0,ignored=0;
    if(!VirtualProtectEx(process,site,1,PAGE_EXECUTE_READWRITE,&previous))return false;
    bool okay=ReadProcessMemory(process,site,&actual,1,&count) && count==1 && actual==expected;
    if(okay)okay=WriteProcessMemory(process,site,&replacement,1,&count) && count==1 &&
        FlushInstructionCache(process,site,1) && ReadProcessMemory(process,site,&actual,1,&count) && count==1 && actual==replacement;
    bool restored=VirtualProtectEx(process,site,1,previous,&ignored)!=FALSE;
    return okay && restored; // caller kills the still-stopped child on false
}
inline EntryGateResult RunEntryGate(const EntryGateInputs& input, VerifyEntryHealth verify, void* opaque) {
    static_assert(sizeof(void*)==4,"entry gate requires the x86 bootstrap build");
    EntryGateResult result;
    if(!input.executable||!input.command_line||!input.directory||!input.executable_file||
       input.executable_file==INVALID_HANDLE_VALUE||!input.proxy_file||input.proxy_file==INVALID_HANDLE_VALUE||
       !input.entry_rva||input.entry_original==0xCC||!input.initializer_rva||
       input.initializer_rva>=input.proxy_image_size||!input.timeout_ms||input.timeout_ms>60000||!verify)return result;
    HANDLE job=CreateJobObjectW(nullptr,nullptr);
    if(!job){result.failure="job_create";return result;}
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limit={};
    limit.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    if(!SetInformationJobObject(job,JobObjectExtendedLimitInformation,&limit,sizeof(limit))) {
        CloseHandle(job);result.failure="job_limit";return result;
    }
    STARTUPINFOW startup={};startup.cb=sizeof(startup);
    PROCESS_INFORMATION child={};
    if(!CreateProcessW(input.executable,input.command_line,nullptr,nullptr,FALSE,
        DEBUG_ONLY_THIS_PROCESS|CREATE_UNICODE_ENVIRONMENT|CREATE_NO_WINDOW,
        input.environment,input.directory,&startup,&child)) {
        CloseHandle(job);result.failure="process_create";return result;
    }
    result.pid=child.dwProcessId;
    if(!DebugSetProcessKillOnExit(TRUE)) {
        if(!TerminateProcess(child.hProcess,0x4E430002))AbortBootstrap("cleanup");
        AbortBootstrap("cleanup");
    }
    HANDLE remote=nullptr;DWORD remote_id=0;
    uintptr_t proxy_base=0;void* entry=nullptr;
    bool initial_break=false,suspended=false,terminal=false,pending=false,detached=false;
    DEBUG_EVENT event={};
    const ULONGLONG deadline=GetTickCount64()+input.timeout_ms;
    result.failure="bootstrap_timeout";
    while(GetTickCount64()<deadline) {
        if(!WaitForDebugEvent(&event,50)) {
            if(GetLastError()==ERROR_SEM_TIMEOUT)continue;
            result.failure="debug_wait";break;
        }
        pending=true;bool stop=false,finished=false;
        if(event.dwProcessId!=child.dwProcessId) {result.failure="foreign_debug_event";stop=true;}
        else switch(event.dwDebugEventCode) {
        case CREATE_PROCESS_DEBUG_EVENT: {
            FILETIME created,exited,kernel,user;
            if(!SameFileIdentity(input.executable_file,event.u.CreateProcessInfo.hFile)||
               !AssignProcessToJobObject(job,child.hProcess)||
               !GetProcessTimes(child.hProcess,&created,&exited,&kernel,&user)) {
                result.failure="process_identity";stop=true;break;
            }
            result.created=(static_cast<unsigned long long>(created.dwHighDateTime)<<32)|created.dwLowDateTime;
            uintptr_t base=reinterpret_cast<uintptr_t>(event.u.CreateProcessInfo.lpBaseOfImage);
            if(base>UINTPTR_MAX-input.entry_rva || !MatchesRemoteEntry(child.hProcess,base,input.entry_rva)){result.failure="entry_range";stop=true;break;}
            entry=reinterpret_cast<void*>(base+input.entry_rva);
            if(!ReplaceRemoteByte(child.hProcess,entry,input.entry_original,0xCC)) {
                result.failure="entry_breakpoint";stop=true;
            }
            break;
        }
        case LOAD_DLL_DEBUG_EVENT:
            if(SameFileIdentity(input.proxy_file,event.u.LoadDll.hFile)) {
                if(proxy_base){result.failure="duplicate_proxy";stop=true;}
                proxy_base=reinterpret_cast<uintptr_t>(event.u.LoadDll.lpBaseOfDll);
            }
            break;
        case UNLOAD_DLL_DEBUG_EVENT:
            if(proxy_base==reinterpret_cast<uintptr_t>(event.u.UnloadDll.lpBaseOfDll)) {
                result.failure="proxy_unloaded";stop=true;
            }
            break;
        case EXCEPTION_DEBUG_EVENT:
            if(event.dwThreadId!=child.dwThreadId || event.u.Exception.ExceptionRecord.ExceptionCode!=EXCEPTION_BREAKPOINT || suspended) {
                result.failure="startup_exception";stop=true;break;
            }
            if(event.u.Exception.ExceptionRecord.ExceptionAddress==entry && initial_break) {
                if(!proxy_base||proxy_base>UINTPTR_MAX-input.proxy_image_size ||
                   !ReplaceRemoteByte(child.hProcess,entry,0xCC,input.entry_original)) {
                    result.failure="entry_restore";stop=true;break;
                }
                CONTEXT context={};context.ContextFlags=CONTEXT_CONTROL;
                if(!GetThreadContext(child.hThread,&context)||context.Eip!=reinterpret_cast<DWORD>(entry)+1) {
                    result.failure="entry_context";stop=true;break;
                }
                context.Eip=reinterpret_cast<DWORD>(entry);
                if(!SetThreadContext(child.hThread,&context)||SuspendThread(child.hThread)!=0) {
                    result.failure="entry_suspend";stop=true;break;
                }
                suspended=true;
                remote=CreateRemoteThread(child.hProcess,nullptr,0,
                    reinterpret_cast<LPTHREAD_START_ROUTINE>(proxy_base+input.initializer_rva),nullptr,0,&remote_id);
                if(!remote){result.failure="initializer_thread";stop=true;}
            } else if(!initial_break)initial_break=true;
            else {result.failure="unexpected_breakpoint";stop=true;}
            break;
        case EXIT_THREAD_DEBUG_EVENT:
            if(remote && event.dwThreadId==remote_id) {
                result.initializer_exit=event.u.ExitThread.dwExitCode;
                if(result.initializer_exit!=0){result.failure="initializer_failed";stop=true;}
                else finished=true;
            } else if(event.dwThreadId==child.dwThreadId) {result.failure="primary_exited";stop=true;}
            break;
        case EXIT_PROCESS_DEBUG_EVENT:
            terminal=true;result.failure="process_exited";stop=true;break;
        case RIP_EVENT:
            result.failure="debug_rip";stop=true;break;
        }
        CloseDebugFile(event);
        // No failing event may release application execution before termination.
        if(stop)break;
        if(!ContinueDebugEvent(event.dwProcessId,event.dwThreadId,DBG_CONTINUE)) {
            result.failure="debug_continue";break;
        }
        pending=false;
        if(finished) {
            if(GetTickCount64()>=deadline || !verify(child.hProcess,result,deadline,opaque) || GetTickCount64()>=deadline) {
                result.failure="runtime_health";break;
            }
            if(!DebugActiveProcessStop(child.dwProcessId)) {result.failure="debug_detach";break;}
            detached=true;
            // Windows closes debugger event process/thread handles on detach;
            // do not close stale numeric handles (they can be reused). Independent
            // CreateProcess/CreateRemoteThread handles remain ours.
            if(ResumeThread(child.hThread)!=1){result.failure="entry_resume";break;}
            // Transfer containment; do not disarm it between detach/resume or
            // add another fallible gate after application execution is allowed.
            result.process=child.hProcess;child.hProcess=nullptr;
            result.job=job;job=nullptr;
            result.started=true;result.failure="";break;
        }
    }
    if(!result.started) {
        if(!terminal && !TerminateProcess(child.hProcess,0x4E430002) &&
           WaitForSingleObject(child.hProcess,0)!=WAIT_OBJECT_0) {
            DWORD code=STILL_ACTIVE;
            if(!GetExitCodeProcess(child.hProcess,&code)||code==STILL_ACTIVE)AbortBootstrap("terminate");
        }
        if(pending) {
            if(!ContinueDebugEvent(event.dwProcessId,event.dwThreadId,DBG_CONTINUE))AbortBootstrap("cleanup");
            pending=false;
        }
        if(!detached && !terminal) {
            const ULONGLONG cleanup=GetTickCount64()+5000;
            bool exited=false;
            while(GetTickCount64()<cleanup) {
                DEBUG_EVENT next={};
                if(!WaitForDebugEvent(&next,50)) {
                    if(GetLastError()!=ERROR_SEM_TIMEOUT)AbortBootstrap("cleanup");
                    continue;
                }
                CloseDebugFile(next);
                if(!ContinueDebugEvent(next.dwProcessId,next.dwThreadId,DBG_CONTINUE))AbortBootstrap("cleanup");
                if(next.dwDebugEventCode==EXIT_PROCESS_DEBUG_EVENT){exited=true;break;}
            }
            if(!exited)AbortBootstrap("cleanup");
        }
        if(WaitForSingleObject(child.hProcess,5000)!=WAIT_OBJECT_0)AbortBootstrap("cleanup");
    }
    if(job)CloseHandle(job);
    if(remote)CloseHandle(remote);
    CloseHandle(child.hThread);if(child.hProcess)CloseHandle(child.hProcess);
    return result;
}
}
