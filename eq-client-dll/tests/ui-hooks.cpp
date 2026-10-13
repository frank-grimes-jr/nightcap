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
static std::vector<std::string> displayed_messages;
static void* expected_eq = nullptr;
static void __fastcall fake_request_sender(void* self, void*, int channel, const char* target, const char* text, int unknown) {
    assert(self == expected_eq && channel == 8 && target == nullptr && unknown == 0);
    sent_requests.emplace_back(text);
}
static void __fastcall fake_chat(void*, void*, const char* message, int, bool, bool) { ++displayed_lines;displayed_messages.emplace_back(message); }
static std::map<std::string, void*> management_controls;
static unsigned native_pet_calls = 0;
static nightcap::client_ui::EqString* __fastcall fake_ui_assign(nightcap::client_ui::EqString* self, void*, const char* text) {
    self->rep = const_cast<char*>(text); return self;
}
static void* __fastcall fake_ui_child(void*, void*, const nightcap::client_ui::EqString* id) {
    auto it = management_controls.find(static_cast<const char*>(id->rep));
    return it == management_controls.end() ? nullptr : it->second;
}
static int __fastcall fake_pet_window(void*, void*, void*, uint32_t, void*) { ++native_pet_calls; return 7; }
static void* available_self = nullptr;
static unsigned available_command = 0;
static bool native_available = false;
static bool __fastcall fake_pet_available(void* self, void*, unsigned command) {
    available_self = self; available_command = command;
    return native_available;
}
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

struct ScribeCharacter { void** table; unsigned level; };
static unsigned __fastcall ScribeCharacterLevel(void* self,void*) {
    return static_cast<ScribeCharacter*>(self)->level;
}
static bool NativeScribeLevelCheck(nightcap::client_ui::SpellLevel hook,void* spell,unsigned level) {
    // Exact RVA 0x35E081..0x35E09C: call the level accessor, read character
    // level through its vtable, then branch on the signed comparison. Only
    // relocate the call and rejection destination; keep register usage intact.
    const BYTE native[]={0x50,0x8B,0xCE,0xE8,0x77,0x16,0xD5,0xFF,0x8B,0x17,
        0x0F,0xB6,0xD8,0x8B,0x42,0x68,0x8B,0xCF,0xFF,0xD0,0x3B,0xD8,
        0x0F,0x8F,0x20,0x04,0,0};
    void* table[27]={};table[26]=reinterpret_cast<void*>(&ScribeCharacterLevel);
    ScribeCharacter character{table,level};
    std::vector<BYTE> code={0x53,0x56,0x57}; // save EBX/ESI/EDI
    const auto immediate=[&](BYTE opcode,uint32_t value) {
        code.push_back(opcode);const auto bytes=reinterpret_cast<const BYTE*>(&value);
        code.insert(code.end(),bytes,bytes+4);
    };
    immediate(0xBE,reinterpret_cast<uint32_t>(spell));
    immediate(0xBF,reinterpret_cast<uint32_t>(&character));
    immediate(0xB8,2); // primary Cleric, held Magician supplied by NCUI1
    const auto start=code.size();code.insert(code.end(),native,native+sizeof(native));
    immediate(0xB8,1);
    const BYTE success[]={0x5F,0x5E,0x5B,0xC3};code.insert(code.end(),success,success+sizeof(success));
    const auto rejected=code.size();
    const BYTE failure[]={0x33,0xC0,0x5F,0x5E,0x5B,0xC3};code.insert(code.end(),failure,failure+sizeof(failure));
    auto memory=static_cast<BYTE*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));
    assert(memory);memcpy(memory,code.data(),code.size());
    const auto call=static_cast<int32_t>(reinterpret_cast<uintptr_t>(hook)-reinterpret_cast<uintptr_t>(memory+start+8));
    const auto branch=static_cast<int32_t>(rejected-start-sizeof(native));
    memcpy(memory+start+4,&call,4);memcpy(memory+start+24,&branch,4);
    assert(FlushInstructionCache(GetCurrentProcess(),memory,code.size()));
    const bool result=reinterpret_cast<int (__cdecl *)()>(memory)()!=0;
    VirtualFree(memory,0,MEM_RELEASE);return result;
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
    const auto scribe_level=reinterpret_cast<SpellLevel>(&ScribeSpellLevelHook);
    assert(scribe_level(spell,2)==1 && scribe_level(spell,13)==255);
    assert(scribe_level(nullptr,2)==255);
    assert(!NativeScribeLevelCheck(level_hook,spell,1)); // old level-17 rejection
    assert(NativeScribeLevelCheck(scribe_level,spell,1));
    assert(!NativeScribeLevelCheck(level_hook,spell,16));
    assert(NativeScribeLevelCheck(level_hook,spell,17)); // ordinary levels stay real
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
    assert(scribe_level(spell,2)==255); // class release removes early scribing
    assert(!NativeScribeLevelCheck(scribe_level,spell,50));
    *reinterpret_cast<uint32_t*>(spell+0x174)=44999;
    assert(scribe_level(spell,2)==255);
    *reinterpret_cast<uint32_t*>(spell+0x174)=4;
    item_spell=44999; assert(mask_hook(item,false,false)==0); item_spell=4;
    item_type=0; item_mask=1u<<10;
    assert(mask_hook(item,false,false)==((1u<<10)|(1u<<1)));
    *reinterpret_cast<uint32_t*>(player+0x148)=8; // old metadata cannot affect next spawn
    assert(level_hook(spell,2)==123 && mask_hook(item,false,false)==item_mask);
    assert(scribe_level(spell,2)==255); // stale character snapshot
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

// The native pet-arrival caller at RoF2 VA 0x70F74F reuses ECX for the
// preference getter at 0x70F400 without reloading the pet-window pointer.
static bool CheckPetAvailableRegisters(void* self, unsigned command) {
    auto hook = &nightcap::client_ui::PetAvailableHook;
    uintptr_t before = 0, after = 0, returned_self = 0, returned_edx = 0;
    unsigned char result = 0;
    __asm {
        mov before, esp
        mov ecx, self
        mov edx, 13579BDFh
        push command
        call hook
        mov result, al
        mov returned_self, ecx
        mov returned_edx, edx
        mov after, esp
    }
    if (returned_self != reinterpret_cast<uintptr_t>(self) ||
        returned_edx != 0x13579BDF || before != after) {
        std::cerr << "Pet availability hook corrupted native caller registers/stack\n";
        std::exit(2);
    }
    return result != 0;
}

static void TestPetManagementABI() {
    using namespace nightcap::client_ui;
    auto host = static_cast<BYTE*>(VirtualAlloc(nullptr,0xA68000,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));
    assert(host);
    alignas(4) BYTE eq[0x600] = {}, player[0x150] = {}, profile[4] = {}, connection[4] = {};
    base = reinterpret_cast<uintptr_t>(host);
    *reinterpret_cast<void**>(host+0xA67CCC) = eq;
    *reinterpret_cast<void**>(host+0x9D2630) = player;
    *reinterpret_cast<void**>(host+0x9D261C) = profile;
    *reinterpret_cast<void**>(host+0x9D25AC) = connection;
    *reinterpret_cast<int*>(eq+0x5C8) = 5;
    *reinterpret_cast<uint32_t*>(player+0x148) = 7;
    memcpy(player+0xA4,"Test",5);
    JumpTo(host+kUIStringAssignRva, reinterpret_cast<void*>(&fake_ui_assign));
    JumpTo(host+kUIChildRva, reinterpret_cast<void*>(&fake_ui_child));
    original_pet_window = reinterpret_cast<InventoryNotify>(&fake_pet_window);
    original_pet_available = reinterpret_cast<PetAvailable>(&fake_pet_available);
    send_request = reinterpret_cast<SendRequest>(&fake_request_sender);
    expected_eq = eq; sent_requests.clear(); pet_management.Clear();
    ChatHook(eq,nullptr,"[NCPM1]|77|1|19|22|0|7|54657374|0|3|10|101|95|537069726974|11|102|80|426f6e6573|13|103|100|5761746572",0,false,false);
    assert(CurrentManagementIdentity());
    auto available = &CheckPetAvailableRegisters;
    for (int repeat = 0; repeat < 1000; ++repeat) assert(available(eq,2));
    assert(!available(eq,30) && !available(eq,34));
    assert(available_self == eq && available_command == 34);
    native_available = true;
    assert(available(eq,30) && available_self == eq && available_command == 30);
    native_available = false;
    auto notify = reinterpret_cast<InventoryNotify>(&PetWindowHook);
    management_controls["NCPM_Pet1Name"] = reinterpret_cast<void*>(1);
    management_controls["NCPM_All"] = reinterpret_cast<void*>(2);
    assert(notify(eq,reinterpret_cast<void*>(1),1,nullptr) == 1);
    assert(sent_requests.back() == "#nightcappet select 102 77");
    assert(notify(eq,reinterpret_cast<void*>(2),1,nullptr) == 1);
    assert(sent_requests.back() == "#nightcappet select 0 77");
    const unsigned commands[] = {2,4,5,12,6,9,31,28,15,18,24,21,0,29};
    for (unsigned i = 0; i < 14; ++i) {
        auto sender = reinterpret_cast<void*>(i+3);
        management_controls["NCPM_Command"+std::to_string(i)] = sender;
        assert(notify(eq,sender,1,nullptr) == 1);
        assert(sent_requests.back() == "#nightcappet order " + std::to_string(commands[i]) + " 77");
    }
    assert(native_pet_calls == 0); // no singular pet/profile gate was consulted
    const auto prior_count = sent_requests.size();
    assert(notify(eq,reinterpret_cast<void*>(1),0x17,nullptr) == 1);
    assert(native_pet_calls == 0 && sent_requests.size() == prior_count); // roster drag cannot create Attack hotbutton
    const unsigned legacy_commands[] = {0,1,2,3,4,5,6,9,31,12,15,18,21,24,27,28,29};
    for (unsigned i = 0; i < 17; ++i) {
        auto sender = reinterpret_cast<void*>(i+100);
        reinterpret_cast<void**>(eq+0x26C)[i] = sender;
        assert(notify(eq,sender,1,nullptr) == 1);
        assert(sent_requests.back() == "#nightcappet order " + std::to_string(legacy_commands[i]) + " 77");
    }
    assert(notify(eq,reinterpret_cast<void*>(99),1,nullptr) == 7 && native_pet_calls == 1);
    const auto count = sent_requests.size();
    next_management_refresh = GetTickCount64()+3000;
    management_received = GetTickCount64()-6000;
    assert(!available(eq,2));
    assert(available_self == eq && available_command == 2);
    assert(notify(eq,reinterpret_cast<void*>(3),1,nullptr) == 1 && sent_requests.size() == count);
    management_received = GetTickCount64();
    *reinterpret_cast<uint32_t*>(player+0x148) = 8;
    assert(!available(eq,2));
    pet_management.Clear();
    *reinterpret_cast<uint32_t*>(player+0x148) = 7;
    assert(!available(eq,2)); // an empty roster must still use the native predicate
    pet_management.Clear(); management_controls.clear(); send_request = nullptr;
    VirtualFree(host,0,MEM_RELEASE); base = 0;
}

static void TestMerchantSellAllABI() {
    using namespace nightcap::client_ui;
    auto host = static_cast<BYTE*>(VirtualAlloc(nullptr,0xA68000,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));
    assert(host);
    alignas(4) BYTE eq[0x600]={}, player[0x150]={}, profile[4]={}, connection[4]={};
    base = reinterpret_cast<uintptr_t>(host);
    *reinterpret_cast<void**>(host+0xA67CCC)=eq;
    *reinterpret_cast<void**>(host+0x9D2630)=player;
    *reinterpret_cast<void**>(host+0x9D261C)=profile;
    *reinterpret_cast<void**>(host+0x9D25AC)=connection;
    *reinterpret_cast<int*>(eq+0x5C8)=5;
    *reinterpret_cast<uint32_t*>(player+0x148)=7;
    memcpy(player+0xA4,"Test",5);
    JumpTo(host+kUIStringAssignRva,reinterpret_cast<void*>(&fake_ui_assign));
    JumpTo(host+kUIChildRva,reinterpret_cast<void*>(&fake_ui_child));
    original_merchant=reinterpret_cast<InventoryNotify>(&fake_pet_window);
    send_request=reinterpret_cast<SendRequest>(&fake_request_sender);
    expected_eq=eq; sent_requests.clear(); native_pet_calls=0;
    auto notify=reinterpret_cast<InventoryNotify>(&MerchantWindowHook);
    auto button=reinterpret_cast<void*>(123);
    management_controls["NC_MerchantSellAll"]=button;
    // Actual x86 notification ABI, many calls to catch stack imbalance.
    for (int i=0;i<1000;++i) assert(notify(eq,button,1,nullptr)==1);
    assert(sent_requests.size()==1000 && native_pet_calls==0);
    for (const auto& request:sent_requests) assert(request=="#sellall");
    for (uint32_t message:{0u,2u,3u,0x17u}) assert(notify(eq,button,message,nullptr)==1);
    assert(sent_requests.size()==1000); // only left-click submits
    assert(notify(eq,reinterpret_cast<void*>(124),1,nullptr)==7);
    assert(notify(eq,nullptr,1,nullptr)==7 && native_pet_calls==2);
    *reinterpret_cast<int*>(eq+0x5C8)=1;
    assert(notify(eq,button,1,nullptr)==1 && sent_requests.size()==1000);
    *reinterpret_cast<int*>(eq+0x5C8)=5;
    *reinterpret_cast<void**>(host+0x9D25AC)=nullptr;
    assert(notify(eq,button,1,nullptr)==1 && sent_requests.size()==1000);
    // Skin reload replaced the control; the old address cannot issue a sale.
    management_controls["NC_MerchantSellAll"]=reinterpret_cast<void*>(125);
    assert(notify(eq,button,1,nullptr)==7 && native_pet_calls==3);
    management_controls.clear(); send_request=nullptr;
    sent_requests.clear(); native_pet_calls=0;
    VirtualFree(host,0,MEM_RELEASE); base=0;
}

static void* expected_craft_window=nullptr;
static void* expected_combine=nullptr;
static void* expected_autoinventory=nullptr;
static uint32_t selected_recipe=47;
static int* native_craft_pending=nullptr;
static unsigned craft_calls=0,autoinventory_calls=0,other_craft_calls=0,craft_frames=0;
static bool reject_native_craft=false;
static const uint32_t* __fastcall fake_craft_selected(void* self,void*) {
    assert(self==expected_craft_window);return &selected_recipe;
}
static int __fastcall fake_craft_notify(void* self,void*,void* sender,uint32_t message,void*) {
    assert(self==expected_craft_window);
    if(sender==expected_combine && message==1) {
        ++craft_calls;if(!reject_native_craft)++*native_craft_pending;
    } else if(sender==expected_autoinventory && message==1)++autoinventory_calls;
    else ++other_craft_calls;
    return 17;
}
static int __fastcall fake_craft_frame(void* self,void*) {
    assert(self==expected_craft_window);++craft_frames;return 19;
}
static void TestTradeskillABI() {
    using namespace nightcap::client_ui;
    auto host=static_cast<BYTE*>(VirtualAlloc(nullptr,0xA68000,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));
    assert(host);
    alignas(4) BYTE eq[0x600]={},player[0x150]={},profile[4]={},connection[4]={},window[0x430]={};
    alignas(4) BYTE combine[0x30]={},autoinventory[0x30]={},container[4]={};
    base=reinterpret_cast<uintptr_t>(host);
    *reinterpret_cast<void**>(host+0xA67CCC)=eq;
    *reinterpret_cast<void**>(host+0x9D2630)=player;
    *reinterpret_cast<void**>(host+0x9D261C)=profile;
    *reinterpret_cast<void**>(host+0x9D25AC)=connection;
    *reinterpret_cast<int*>(eq+0x5C8)=5;
    *reinterpret_cast<uint32_t*>(player+0x148)=7;memcpy(player+0xA4,"Crafter",8);
    window[0x196]=1;combine[0x1a]=1;
    *reinterpret_cast<void**>(window+0x424)=container;
    *reinterpret_cast<void**>(window+0x278)=combine;
    *reinterpret_cast<void**>(window+0x240)=autoinventory;
    native_craft_pending=reinterpret_cast<int*>(host+0xA635AC);
    expected_craft_window=window;expected_combine=combine;expected_autoinventory=autoinventory;
    JumpTo(host+kUIStringAssignRva,reinterpret_cast<void*>(&fake_ui_assign));
    JumpTo(host+kUIChildRva,reinterpret_cast<void*>(&fake_ui_child));
    JumpTo(host+kCraftSelectedRva,reinterpret_cast<void*>(&fake_craft_selected));
    original_tradeskill=reinterpret_cast<InventoryNotify>(&fake_craft_notify);
    original_tradeskill_frame=reinterpret_cast<TradeskillFrame>(&fake_craft_frame);
    original_chat=reinterpret_cast<DisplayChat>(&fake_chat);
    const auto notify=reinterpret_cast<InventoryNotify>(&TradeskillWindowHook);
    const auto frame=reinterpret_cast<TradeskillFrame>(&TradeskillFrameHook);
    auto all=reinterpret_cast<void*>(101),stop=reinterpret_cast<void*>(102),search=reinterpret_cast<void*>(103);
    management_controls["NC_CraftAll"]=all;management_controls["NC_CraftStop"]=stop;
    management_controls["CombineButton"]=combine;
    craft_repeat.Reset();craft_calls=autoinventory_calls=other_craft_calls=craft_frames=0;
    void* found=nullptr;uint32_t recipe=0;bool ready=false;
    assert(ReadCraftContext(window,found,recipe,ready)&&found==container&&recipe==47&&ready);
    selected_recipe=0;assert(!ReadCraftContext(window,found,recipe,ready));selected_recipe=47;
    window[0x196]=0;assert(!ReadCraftContext(window,found,recipe,ready));window[0x196]=1;
    combine[0x1a]=0;assert(ReadCraftContext(window,found,recipe,ready)&&!ready);combine[0x1a]=1;
    *native_craft_pending=1;assert(ReadCraftContext(window,found,recipe,ready)&&!ready);*native_craft_pending=0;
    for(uint32_t message:{0u,2u,3u,0x17u})assert(notify(window,all,message,nullptr)==1);
    assert(craft_calls==0);
    assert(notify(window,all,1,nullptr)==1&&craft_calls==1&&craft_repeat.Active()&&craft_repeat.Pending());
    assert(craft_window==window&&craft_container==container&&craft_recipe==47&&craft_spawn==7);
    for(int i=0;i<1000;++i)assert(frame(window)==19);
    assert(craft_calls==1&&autoinventory_calls==0&&craft_frames==1000); // frames cannot replay without server completion
    assert(notify(window,stop,1,nullptr)==1&&!craft_repeat.Active()&&craft_repeat.Pending());
    assert(notify(window,all,1,nullptr)==1&&craft_calls==1);
    assert(notify(window,combine,1,nullptr)==1&&craft_calls==1); // manual native combine blocked while outstanding
    assert(ConsumeCraftReply("[NCTS1]|8|47|1")&&craft_repeat.Pending());
    assert(ConsumeCraftReply("[NCTS1]|7|48|1")&&craft_repeat.Pending());
    assert(ConsumeCraftReply("[NCTS1]|4294967303|47|1")&&craft_repeat.Pending());
    assert(!ConsumeCraftReply("ordinary chat"));
    *native_craft_pending=0;assert(ConsumeCraftReply("[NCTS1]|7|47|1")&&!craft_repeat.Pending());
    assert(frame(window)==19&&craft_calls==1&&autoinventory_calls==0); // stopped result does not resume
    reject_native_craft=true;
    assert(notify(window,all,1,nullptr)==1&&craft_calls==2);
    assert(!craft_repeat.Active()&&!craft_repeat.Pending()&&!craft_repeat.Uncertain());
    reject_native_craft=false;
    assert(notify(window,all,1,nullptr)==1&&craft_calls==3&&craft_repeat.Pending());
    *native_craft_pending=0;assert(ConsumeCraftReply("[NCTS1]|7|47|0")&&!craft_repeat.Active());

    // Seed elapsed time deterministically, then exercise the actual frame hook
    // through both native auto-inventory and the next native combine dispatch.
    craft_repeat.Reset();assert(craft_repeat.Start(GetTickCount64()-2300,7,47));
    assert(ConsumeCraftReply("[NCTS1]|7|47|1"));
    assert(frame(window)==19&&autoinventory_calls==1&&craft_calls==3);
    Sleep(320);
    assert(frame(window)==19&&craft_calls==4&&craft_repeat.Pending());
    assert(ConsumeCraftReply("[NCTS1]|7|47|1")&&craft_repeat.Completed()==2);
    assert(ConsumeCraftReply("[NCTS1]|7|47|1")&&craft_repeat.Completed()==2); // duplicate completion ignored
    *native_craft_pending=0;
    for(uint32_t message:{1u,3u,6u,15u}) {
        craft_repeat.Reset();assert(craft_repeat.Start(GetTickCount64(),7,47));
        assert(notify(window,search,message,nullptr)==17&&!craft_repeat.Active()&&craft_repeat.Pending());
        assert(ConsumeCraftReply("[NCTS1]|7|47|1")&&!craft_repeat.Pending());
    }
    assert(other_craft_calls==4);
    for(int changed=0;changed<4;++changed) {
        craft_repeat.Reset();assert(craft_repeat.Start(GetTickCount64(),7,47));
        if(changed==0)selected_recipe=48;
        if(changed==1)*reinterpret_cast<void**>(window+0x424)=eq;
        if(changed==2)*reinterpret_cast<uint32_t*>(player+0x148)=8;
        if(changed==3)window[0x196]=0;
        assert(frame(window)==19&&!craft_repeat.Active()&&craft_repeat.Pending());
        selected_recipe=47;*reinterpret_cast<void**>(window+0x424)=container;
        *reinterpret_cast<uint32_t*>(player+0x148)=7;window[0x196]=1;
    }
    craft_repeat.Reset();assert(craft_repeat.Start(GetTickCount64()-15001,7,47));
    assert(frame(window)==19&&craft_repeat.Uncertain()&&!craft_repeat.Pending());
    assert(displayed_messages.back().find("Zone or relog")!=std::string::npos);
    const auto before=craft_calls;assert(notify(window,all,1,nullptr)==1&&craft_calls==before);
    assert(displayed_messages.back().find("Zone or relog")!=std::string::npos);
    craft_repeat.Reset();management_controls.clear();original_tradeskill=nullptr;original_tradeskill_frame=nullptr;
    craft_window=craft_container=nullptr;craft_recipe=craft_spawn=0;craft_name[0]=0;
    displayed_lines=0;displayed_messages.clear();
    VirtualFree(host,0,MEM_RELEASE);base=0;
}

int main() {
    TestTradeskillABI();
    TestMerchantSellAllABI();
    TestSpellAccessABI();
    TestSilentRequests();
    TestPetManagementABI();
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
