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

static std::vector<std::string> sent_requests;
static unsigned displayed_lines = 0;
static void* expected_eq = nullptr;
static void __fastcall fake_request_sender(void* self, void*, int channel, const char* target, const char* text, int unknown) {
    assert(self == expected_eq && channel == 8 && target == nullptr && unknown == 0);
    sent_requests.emplace_back(text);
}
static void __fastcall fake_chat(void*, void*, const char*, int, bool, bool) { ++displayed_lines; }
static unsigned stock_level_calls=0, item_calls=0;
static uint32_t item_mask=65535;
static int item_type=20, item_spell=4;
static bool last_flag1=false, last_flag2=false;
static bool native_use_result=true, use_raises=false;
static bool use_required=false,use_output=false;
static uint8_t __fastcall fake_spell_level(void*,void*,int) { ++stock_level_calls; return 123; }
static uint32_t __fastcall fake_item_classes(void*,void*,bool first,bool second) {
    ++item_calls; last_flag1=first; last_flag2=second; return item_mask;
}
static int __fastcall fake_item_type(void*,void*) { return item_type; }
static int __fastcall fake_item_spell(void*,void*,int type) { assert(type==4); return item_spell; }
static BYTE __fastcall fake_can_use(void*,void*,const void* item_ref,bool required,bool output) {
    using namespace nightcap::client_ui;
    const auto item=*reinterpret_cast<const void* const*>(item_ref);
    assert(ActiveSpellItem()==item);
    use_required=required;use_output=output;
    if(use_raises) RaiseException(0xE0123456,0,0,nullptr);
    const auto mask=ScribeClassMask(item_mask,item,true,false);
    return native_use_result && ((mask&(1u<<1))!=0);
}
static void ExerciseScribeException(void* character,const void* item_ref) {
    bool caught=false;
    __try { nightcap::client_ui::CanUseSpellItem(character,nullptr,item_ref,true,true); }
    __except(EXCEPTION_EXECUTE_HANDLER) { caught=true; }
    assert(caught);
}
static void JumpTo(BYTE* address, void* function) {
    DWORD old=0;
    assert(VirtualProtect(address,5,PAGE_EXECUTE_READWRITE,&old));
    address[0]=0xE9;
    const auto delta=static_cast<int32_t>(reinterpret_cast<uintptr_t>(function)-reinterpret_cast<uintptr_t>(address+5));
    memcpy(address+1,&delta,4);
    assert(FlushInstructionCache(GetCurrentProcess(),address,5));
}

static void TestSpellAccessABI() {
    using namespace nightcap::client_ui;
    auto host=static_cast<BYTE*>(VirtualAlloc(nullptr,0xA68000,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));
    assert(host);
    alignas(4) BYTE eq[0x600]={},player[0x150]={},spell[0x280]={},item[4]={};
    base=reinterpret_cast<uintptr_t>(host);
    *reinterpret_cast<void**>(host+0xA67CCC)=eq;
    *reinterpret_cast<void**>(host+0x9D2630)=player;
    *reinterpret_cast<int*>(eq+0x5C8)=5;
    *reinterpret_cast<uint32_t*>(player+0x148)=7;
    memcpy(player+0xA4,"Monktest",9);
    *reinterpret_cast<uint32_t*>(spell+0x174)=4;
    assert(state.Consume("[NCUI1]S|1|19|22|0|7|2|13|11|Monktest"));
    original_spell_level=reinterpret_cast<SpellLevel>(&fake_spell_level);
    const auto level_hook=reinterpret_cast<SpellLevel>(&SpellLevelHook);
    for(int i=0;i<1000;++i) assert(level_hook(spell,2)==17);
    assert(stock_level_calls==0 && level_hook(spell,13)==123 && stock_level_calls==1);
    using Classes=uint32_t (__thiscall *)(void*,bool,bool);
    JumpTo(host+kItemClassesRva,reinterpret_cast<void*>(&fake_item_classes));
    JumpTo(host+kItemTypeRva,reinterpret_cast<void*>(&fake_item_type));
    JumpTo(host+kItemSpellRva,reinterpret_cast<void*>(&fake_item_spell));
    JumpTo(host+kCanUseItemRva,reinterpret_cast<void*>(&fake_can_use));
    const auto mask_hook=reinterpret_cast<Classes>(&MerchantClassesHook);
    for(int i=0;i<1000;++i) {
        assert(mask_hook(item,true,false)==((1u<<12)|(1u<<1)));
        assert(last_flag1 && !last_flag2);
        assert(mask_hook(item,false,false)==((1u<<12)|(1u<<1)));
        assert(!last_flag1 && !last_flag2);
    }
    item_mask=0; assert(mask_hook(item,false,false)==0); item_mask=65535;
    using CanUse=BYTE (__thiscall *)(void*,const void*,bool,bool);
    auto use_hook=reinterpret_cast<CanUse>(&CanUseSpellItem);
    const void* item_ref=item;
    item_mask=1u<<12;
    for(int i=0;i<1000;++i) assert(use_hook(player,&item_ref,true,true)==1);
    assert(use_required && use_output && ActiveSpellItem()==nullptr);
    native_use_result=false;
    assert(use_hook(player,&item_ref,true,true)==0); // native race/deity/level rejection wins
    native_use_result=true;
    ActiveSpellItem()=spell;
    assert(use_hook(player,&item_ref,false,false)==1 && ActiveSpellItem()==spell);
    assert(!use_required && !use_output);
    use_raises=true; ExerciseScribeException(player,&item_ref);
    assert(ActiveSpellItem()==spell); use_raises=false;ActiveSpellItem()=nullptr;
    item_mask=65535;
    assert(state.Consume("[NCUI1]S|2|19|22|0|7|2|0|11|Monktest"));
    assert(level_hook(spell,2)==255 && mask_hook(item,false,false)==(1u<<12));
    item_spell=44999; assert(mask_hook(item,false,false)==0); item_spell=4;
    item_type=0; item_mask=1u<<10;
    assert(mask_hook(item,false,false)==((1u<<10)|(1u<<1)));
    *reinterpret_cast<uint32_t*>(player+0x148)=8; // old metadata cannot affect next spawn
    assert(level_hook(spell,2)==123 && mask_hook(item,false,false)==item_mask);
    *reinterpret_cast<uint32_t*>(player+0x148)=7;
    *reinterpret_cast<int*>(eq+0x5C8)=1;
    assert(level_hook(spell,2)==123 && mask_hook(item,false,false)==item_mask);
    state.Clear(); base=0; original_spell_level=nullptr;
    VirtualFree(host,0,MEM_RELEASE);
}

static void TestSilentRequests() {
    using namespace nightcap::client_ui;
    auto host = static_cast<BYTE*>(VirtualAlloc(nullptr,0xA68000,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));
    assert(host);
    alignas(4) BYTE eq[0x600] = {}, player[0x150] = {};
    base = reinterpret_cast<uintptr_t>(host);
    expected_eq = eq;
    *reinterpret_cast<void**>(host+0xA67CCC) = eq;
    *reinterpret_cast<void**>(host+0x9D2630) = player;
    *reinterpret_cast<void**>(host+0x9D261C) = player;
    *reinterpret_cast<void**>(host+0x9D25AC) = player;
    *reinterpret_cast<int*>(eq+0x5C8) = 5;
    *reinterpret_cast<uint32_t*>(player+0x148) = 7;
    memcpy(player+0xA4,"Zozobra",8);
    send_request = reinterpret_cast<SendRequest>(&fake_request_sender);
    original_chat = reinterpret_cast<DisplayChat>(&fake_chat);
    RequestRefresh(); RequestPetRefresh();
    assert((sent_requests == std::vector<std::string>{"#nightcapui refresh", "#nightcappet view"}));
    RequestRefresh(); RequestPetRefresh();
    assert(sent_requests.size() == 2); // preserve retry throttles
    assert(ExecuteUIRequest("#nightcappet equip 10 0 77"));
    assert(ExecuteUIRequest("#nightcappet remove 10 7 78"));
    assert(ExecuteUIRequest("#nightcappet inspect 10 4 79"));
    assert(sent_requests.back() == "#nightcappet inspect 10 4 79");
    assert(!ExecuteUIRequest(""));
    *reinterpret_cast<int*>(eq+0x5C8) = 1;
    assert(!ExecuteUIRequest("#nightcapui refresh")); // no packets at character select
    *reinterpret_cast<int*>(eq+0x5C8) = 5;
    for (unsigned offset : {0x9D261C,0x9D25AC,0x9D2630,0xA67CCC}) {
        auto ptr = reinterpret_cast<void**>(host+offset); auto saved = *ptr; *ptr = nullptr;
        assert(!ExecuteUIRequest("#nightcapui refresh")); *ptr = saved;
    }
    assert(sent_requests.size() == 5 && displayed_lines == 0);
    ChatHook(eq,nullptr,"You say, 'hello'",307,true,true);
    ChatHook(eq,nullptr,"You cannot change pet armor while fighting.",13,true,true);
    assert(displayed_lines == 2); // ordinary chat and server errors remain visible
    VirtualFree(host,0,MEM_RELEASE); base = 0; send_request = nullptr;
}

int main() {
    TestSpellAccessABI();
    TestSilentRequests();
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
