#include <windows.h>
#include <cstdint>
#include <cstring>
#include <cassert>
#include <iostream>
#include "../src/patch_catalog.h"
#include "../src/ui_hooks.h"

static int __cdecl replacement() { return 99; }

static unsigned skin_assign_calls = 0;
static nightcap::client_ui::EqString* __fastcall fake_skin_assign(nightcap::client_ui::EqString* self, void*, const char* text) {
    assert(strcmp(text,"nightcap")==0);
    ++skin_assign_calls;
    return self;
}

int main() {
    // Both native UI-load branches use CXStr assignment (__thiscall, one stack
    // argument). Existing/custom/missing skin preferences all choose Nightcap;
    // the original input and unrelated layout data remain untouched.
    nightcap::client_ui::skin_assign = reinterpret_cast<nightcap::client_ui::AssignString>(&fake_skin_assign);
    auto skin_hook = reinterpret_cast<nightcap::client_ui::AssignString>(&nightcap::client_ui::SkinHook);
    nightcap::client_ui::EqString selected{};
    for (const char* preference : {"Default", "custom", "nightcap", "", static_cast<const char*>(nullptr)}) {
        assert(skin_hook(&selected,preference)==&selected);
    }
    assert(skin_assign_calls==5);

    // A disposable synthetic host proves relocated entry execution, return
    // value, original trampoline and byte mismatch rejection. No game process.
    const BYTE original[5] = {0xB8,42,0,0,0}; // mov eax,42
    auto memory = static_cast<BYTE*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));
    assert(memory);
    memcpy(memory,original,5); memory[5]=0xC3;
    using Function = int (__cdecl *)();
    assert(reinterpret_cast<Function>(memory)()==42);
    auto trampoline=nightcap::client_ui::EntryHook(reinterpret_cast<uintptr_t>(memory),original,reinterpret_cast<void*>(&replacement));
    assert(trampoline);
    assert(reinterpret_cast<Function>(memory)()==99);
    assert(reinterpret_cast<Function>(trampoline)()==42);
    assert(!nightcap::client_ui::EntryHook(reinterpret_cast<uintptr_t>(memory),original,reinterpret_cast<void*>(&replacement)));
    VirtualFree(memory,0,MEM_RELEASE);
    VirtualFree(trampoline,0,MEM_RELEASE);

    // Actual startup can map eqgame away from 0x400000. Verify the relocated
    // SEH operand and trampoline execution, rather than assuming preferred base.
    const BYTE seh[7] = {0x6A,0xFF,0x68,0x1A,0x13,0x98,0x00};
    for (uintptr_t image_base : {uintptr_t(0x400000), uintptr_t(0xDA0000), uintptr_t(0x200000)}) {
        BYTE relocated[7];
        assert(nightcap::client_ui::RebaseSEH(seh,image_base,relocated));
        uint32_t table=0;memcpy(&table,relocated+3,4);
        assert(table == uint32_t(0x98131A+image_base-0x400000));
        auto code=static_cast<BYTE*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));
        assert(code);memcpy(code,relocated,7);
        const BYTE tail[]={0x58,0x83,0xC4,0x04,0xC3}; // pop eax; add esp,4; ret
        memcpy(code+7,tail,sizeof(tail));
        const auto address=reinterpret_cast<uintptr_t>(code);
        assert(nightcap::client_ui::MatchSEH(address,seh,image_base));
        assert(!nightcap::client_ui::MatchSEH(address,seh,image_base+0x10000));
        assert(static_cast<uint32_t>(reinterpret_cast<Function>(code)())==table);
        auto bridge=nightcap::client_ui::SEHEntryHook(address,seh,reinterpret_cast<void*>(&replacement),image_base);
        assert(bridge && reinterpret_cast<Function>(code)()==99);
        assert(static_cast<uint32_t>(reinterpret_cast<Function>(bridge)())==table);
        VirtualFree(code,0,MEM_RELEASE);VirtualFree(bridge,0,MEM_RELEASE);
    }

    alignas(4) BYTE window[0x2B0]={}, list[0x200]={}, columns[6*0x3C]={}, text[32]={};
    *reinterpret_cast<void**>(window+0x2A0)=list;
    *reinterpret_cast<int*>(list+0x1D8)=3;
    *reinterpret_cast<int*>(list+0x1E8)=6;
    *reinterpret_cast<void**>(list+0x1EC)=columns;
    *reinterpret_cast<uint32_t*>(text+0x04)=6;
    *reinterpret_cast<uint32_t*>(text+0x08)=5;
    memcpy(text+0x14,"Class",6);
    *reinterpret_cast<void**>(columns+5*0x3C+0x18)=text;
    void* found=nullptr; int rows=0,index=-1;
    assert(nightcap::client_ui::ReadList(window,0,found,rows,index));
    assert(found==list && rows==3 && index==5); // a Timer column cannot overwrite Category
    *reinterpret_cast<void**>(columns+4*0x3C+0x18)=text;
    assert(!nightcap::client_ui::ReadList(window,0,found,rows,index)); // duplicate heading
    *reinterpret_cast<void**>(columns+5*0x3C+0x18)=nullptr;
    assert(nightcap::client_ui::ReadList(window,0,found,rows,index) && index==4);
    *reinterpret_cast<uint32_t*>(text+0x0C)=1;
    assert(!nightcap::client_ui::ReadList(window,0,found,rows,index)); // unsupported encoding
    *reinterpret_cast<uint32_t*>(text+0x0C)=0;
    *reinterpret_cast<uint32_t*>(text+0x04)=5;
    assert(!nightcap::client_ui::ReadList(window,0,found,rows,index)); // missing terminator capacity
    *reinterpret_cast<uint32_t*>(text+0x04)=6;
    *reinterpret_cast<int*>(list+0x1E8)=33;
    assert(!nightcap::client_ui::ReadList(window,0,found,rows,index));
    assert(!nightcap::client_ui::ReadList(nullptr,0,found,rows,index));
    std::cout << "Native UI hook controls passed\n";
}
