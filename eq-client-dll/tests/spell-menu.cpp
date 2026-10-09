#include <windows.h>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>
#include "../src/patch_catalog.h"
#include "../src/ui_hooks.h"

using namespace nightcap::client_ui;
struct MenuRow { uint32_t spell; uint32_t level; };
static std::vector<MenuRow> rows;
static std::vector<std::string> labels;
static unsigned rebuilds=0, frames=0, insertions=0;
static void* menu_window=nullptr;
static void* profile_result=nullptr;
static void* expected_profile_manager=nullptr;
static bool reenter=false;
static bool mutation_fault=false;
static alignas(4) BYTE profile[0x3410]={}, spells[3][0x300]={};
using NativeBuilder=void (__thiscall *)(void*);
using NativeOrder=int (__cdecl *)(const MenuRow*,const MenuRow*);
static NativeBuilder native_builder=nullptr;
static NativeOrder native_order=nullptr;

static void Append32(std::vector<BYTE>& bytes,uint32_t value) {
    const auto first=reinterpret_cast<const BYTE*>(&value); bytes.insert(bytes.end(),first,first+4);
}
static std::vector<BYTE> Hex(const char* hex) {
    std::vector<BYTE> bytes;
    while(*hex) { unsigned value=0; assert(sscanf_s(hex,"%2x",&value)==1);
        bytes.push_back(static_cast<BYTE>(value)); hex+=2; }
    return bytes;
}
static void Relocate(std::vector<BYTE>& bytes,uint32_t from,uint32_t to,unsigned expected=1) {
    unsigned found=0;
    for(size_t i=0;i+4<=bytes.size();++i) { uint32_t value=0; memcpy(&value,bytes.data()+i,4);
        if(value==from) { memcpy(bytes.data()+i,&to,4); ++found; i+=3; } }
    assert(found==expected);
}
static BYTE* Allocate(const std::vector<BYTE>& bytes) {
    auto memory=static_cast<BYTE*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));
    assert(memory); memcpy(memory,bytes.data(),bytes.size()); return memory;
}
static void Redirect(BYTE* site,const void* target,BYTE opcode=0xE8) {
    assert(*site==opcode);
    const auto relative=static_cast<int32_t>(reinterpret_cast<uintptr_t>(target)-reinterpret_cast<uintptr_t>(site+5));
    memcpy(site+1,&relative,4);
}
static int __cdecl Format(char* output,const char* format,int level,const char* name) {
    return sprintf_s(output,160,format,level,name);
}
static BYTE* Spell(unsigned id) {
    for(auto& spell:spells) if(*reinterpret_cast<uint32_t*>(spell+0x174)==id) return spell;
    return nullptr;
}
static uint8_t __fastcall StockLevel(void* spell,void*,int id) {
    assert(id>=1 && id<=16); return static_cast<BYTE*>(spell)[0x246+id];
}
static void* __fastcall CurrentProfile(void* self,void*) {
    assert(self==expected_profile_manager); return profile_result;
}
static BYTE __cdecl ValidSpell(int id) { return Spell(static_cast<unsigned>(id))!=nullptr; }
static void* __fastcall GetSpell(void*,void*,unsigned id) { auto spell=Spell(id); assert(spell); return spell; }
static int __fastcall OriginalFrame(void* self,void*) { assert(self==menu_window); ++frames; return 73; }
static void __fastcall OriginalChat(void*,void*,const char*,int,bool,bool) {}
static void __fastcall OriginalState(void*,void*,int) {}
static void __fastcall ClearMenu(void* self,void*) {
    assert(self==menu_window); ++rebuilds; rows.clear(); labels.clear(); insertions=0;
    if(mutation_fault) RaiseException(0xE0123456,0,0,nullptr);
#ifndef NIGHTCAP_SPELL_MENU_BASELINE
    if(reenter) assert(reinterpret_cast<SpellMenuFrame>(&SpellMenuFrameHook)(self)==73);
#endif
}

#ifndef NIGHTCAP_SPELL_MENU_BASELINE
static void ExpectMutationFailure(SpellMenuFrame frame,void* window) {
    bool caught=false;
    __try { frame(window); }
    __except(GetExceptionCode()==0xE0123456 ? EXCEPTION_EXECUTE_HANDLER : EXCEPTION_CONTINUE_SEARCH) { caught=true; }
    assert(caught && !spell_menu_refreshing);
}
static void VerifyInstallGuardsAndFrameABI(BYTE* host,void* window) {
    assert(kSpellMenuBuildRva==0x248200 && kSpellMenuProfileRva==0x3DB210 && kSpellMenuFrameRva==0x2488A0);
    const BYTE frame_prefix[]={0x56,0x8B,0xF1,0x80,0xBE,0x96,0x01,0,0,0};
    assert(sizeof(kExpectedSpellMenuFrame)==sizeof(frame_prefix) && !memcmp(kExpectedSpellMenuFrame,frame_prefix,sizeof(frame_prefix)));
    memcpy(host+kSpellMenuBuildRva,kExpectedSpellMenuBuild,sizeof(kExpectedSpellMenuBuild));
    memcpy(host+kSpellMenuProfileRva,kExpectedSpellMenuProfile,sizeof(kExpectedSpellMenuProfile));
    memcpy(host+kSpellMenuFrameRva,frame_prefix,sizeof(frame_prefix));
    for(uintptr_t rva:{kSpellMenuBuildRva,kSpellMenuProfileRva,kSpellMenuFrameRva}) {
        host[rva]^=1; assert(!InstallSpellMenu()); host[rva]^=1;
    }
    // Preserve the native push/this/cmp prologue and finish with a deterministic
    // return. Both the installed entry jump and original trampoline execute.
    const BYTE finish[]={0xB8,73,0,0,0,0x5E,0xC3};
    memcpy(host+kSpellMenuFrameRva+sizeof(frame_prefix),finish,sizeof(finish));
    assert(FlushInstructionCache(GetCurrentProcess(),host+kSpellMenuFrameRva,sizeof(frame_prefix)+sizeof(finish)));
    assert(InstallSpellMenu()); spell_menu_dirty=false;
    const auto frame=reinterpret_cast<SpellMenuFrame>(host+kSpellMenuFrameRva);
    for(unsigned repeat=0;repeat<1000;++repeat) assert(frame(window)==73);
    VirtualFree(reinterpret_cast<void*>(original_spell_menu_frame),0,MEM_RELEASE);
}
#endif
static void __fastcall InsertRow(void* self,void*,unsigned spell,unsigned category,unsigned subcategory,unsigned level) {
    assert(self==menu_window && category==125 && (subcategory==1 || subcategory==2)); ++insertions;
    if(subcategory!=1) return;
    MenuRow row{spell,level}; auto place=rows.begin();
    while(place!=rows.end() && !native_order(&*place,&row)) ++place;
    rows.insert(place,row);
}

// Exact native label formatter RVA0x247189..0x2471A8. The level is read
// from the cached menu row, whereas the name is read from the actual spell.
static std::string Render(const MenuRow& row) {
    auto block=Hex("8b4e048bf88d877a02000050518d5424746870539e0052e88a4f290083c410");
    Relocate(block,0x9E5370,reinterpret_cast<uint32_t>("%02d - %s"));
    char result[160]={}; std::vector<BYTE> code={0x56,0x57,0x81,0xEC}; Append32(code,0x200);
    code.push_back(0xBE); Append32(code,reinterpret_cast<uint32_t>(&row));
    code.push_back(0xB8); Append32(code,reinterpret_cast<uint32_t>(Spell(row.spell)));
    const auto start=code.size(); code.insert(code.end(),block.begin(),block.end());
    code.insert(code.end(),{0x8D,0x74,0x24,0x6C,0xBF}); Append32(code,reinterpret_cast<uint32_t>(result));
    code.push_back(0xB9); Append32(code,sizeof(result)); code.insert(code.end(),{0xF3,0xA4,0x81,0xC4});
    Append32(code,0x200); code.insert(code.end(),{0x5F,0x5E,0xC3});
    auto memory=Allocate(code); Redirect(memory+start+0x17,reinterpret_cast<const void*>(&Format));
    assert(FlushInstructionCache(GetCurrentProcess(),memory,code.size()));
    reinterpret_cast<void (__cdecl *)()>(memory)(); VirtualFree(memory,0,MEM_RELEASE); return result;
}
static void __fastcall BuildLabels(void* self,void*) {
    assert(self==menu_window && insertions==rows.size()*2);
    for(const auto& row:rows) labels.push_back(Render(row));
}
static void MakeNativeCode() {
    // Original level ordering branch RVA0x247C39..0x247C41, including its jl.
    // The two branch outcomes return whether an existing row sorts after a new row.
    auto compare=Hex("558b4424088b6c240c8b50043b55047c38");
    compare.insert(compare.end(),{0x33,0xC0,0x5D,0xC3}); compare.resize(9+64,0xCC);
    compare.insert(compare.end(),{0xB8,1,0,0,0,0x5D,0xC3});
    native_order=reinterpret_cast<NativeOrder>(Allocate(compare));
    // Complete native builder RVA0x248200..0x248303: all 720 spellbook slots,
    // native category extraction, existing SpellLevelHook, both insertions,
    // and the final label builder. Only external dependencies are relocated.
    auto build=Hex("83ec0c53555657894c2410e870feffff33dba11c26dd008b48088b51048d4c02088d4904e8e72f190081fbd00200007201cc8bac982025000055e8114fe6ff83c40484c00f849c000000a11c26dd008b48088b51048d4c02088d4904e8af2f190081fbd00200007201cc8b8498202500008b0db046e6008b11508b420cffd08bf08b8e80010000a11c26dd008b96840100008bbe7c010000894c24148b4808895424188b51048d4c02088d4904e85e2f19000fb68074330000508bcee83f74e6ff8b4c24140fb6f056518b4c24185755e88bf6ffff8b5424188b4c241056525755e87af6ffff4381fbd00200000f8c1fffffff8b4c24105f5e5d5b83c40ce98decffff");
    Relocate(build,0xDD261C,static_cast<uint32_t>(base+0x9D261C),3);
    Relocate(build,0xE646B0,static_cast<uint32_t>(base+0xA646B0));
    auto memory=Allocate(build);
    Redirect(memory+0x0B,reinterpret_cast<const void*>(&ClearMenu));
    for(unsigned site:{0x24u,0x5Cu,0xADu}) Redirect(memory+site,reinterpret_cast<const void*>(&CurrentProfile));
    Redirect(memory+0x3A,reinterpret_cast<const void*>(&ValidSpell));
    Redirect(memory+0xBC,reinterpret_cast<const void*>(&SpellLevelHook));
    for(unsigned site:{0xD0u,0xE1u}) Redirect(memory+site,reinterpret_cast<const void*>(&InsertRow));
    Redirect(memory+0xFE,reinterpret_cast<const void*>(&BuildLabels),0xE9);
    assert(FlushInstructionCache(GetCurrentProcess(),memory,build.size()));
    assert(FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(native_order),compare.size()));
    native_builder=reinterpret_cast<NativeBuilder>(memory);
}

int main() {
    const auto started=GetTickCount64();
    auto host=static_cast<BYTE*>(VirtualAlloc(nullptr,0x1200000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));
    assert(host); base=reinterpret_cast<uintptr_t>(host);
    alignas(4) BYTE eq[0x600]={}, player[0x150]={}, character[32]={}, window[0x300]={};
    int32_t vbtable[2]={0,8}; void* spell_vtable[4]={nullptr,nullptr,nullptr,reinterpret_cast<void*>(&GetSpell)};
    void* spell_manager=spell_vtable;
    *reinterpret_cast<void**>(character+8)=vbtable;
    expected_profile_manager=character+20;
    *reinterpret_cast<void**>(host+0x9D261C)=character;
    *reinterpret_cast<void**>(host+0xA646B0)=&spell_manager;
    *reinterpret_cast<void**>(host+0x11D391C)=window;
    *reinterpret_cast<void**>(host+0x91FC84)=window;
    *reinterpret_cast<void**>(host+0xA67CCC)=eq;
    *reinterpret_cast<void**>(host+0x9D2630)=player;
    *reinterpret_cast<int*>(eq+0x5C8)=5;
    *reinterpret_cast<uint32_t*>(player+0x148)=7; memcpy(player+0xA4,"Test",5);
    menu_window=window; profile_result=profile; profile[0x3374]=2;
    auto book=reinterpret_cast<int32_t*>(profile+0x2520); for(unsigned i=0;i<720;++i) book[i]=-1;
    const unsigned ids[]={315,4,15}; const char* names[]={"Elementalkin: Water","Summon Waterstone","Greater Healing"};
    for(unsigned i=0;i<3;++i) {
        book[i]=static_cast<int32_t>(ids[i]); auto spell=spells[i];
        *reinterpret_cast<uint32_t*>(spell+0x174)=ids[i];
        *reinterpret_cast<uint32_t*>(spell+0x17C)=125;
        *reinterpret_cast<uint32_t*>(spell+0x180)=1; *reinterpret_cast<uint32_t*>(spell+0x184)=2;
        memcpy(spell+0x247,NightcapSpellClasses::Find(ids[i])->levels,16);
        strcpy_s(reinterpret_cast<char*>(spell+0x27A),100,names[i]);
    }
    original_spell_level=reinterpret_cast<SpellLevel>(&StockLevel);
    original_chat=reinterpret_cast<DisplayChat>(&OriginalChat); original_state=reinterpret_cast<SetGameState>(&OriginalState);
    MakeNativeCode(); state.Clear(); native_builder(window);
    assert(labels[0]=="255 - Elementalkin: Water" && labels[1]=="255 - Summon Waterstone" && labels[2]=="20 - Greater Healing");
    ChatHook(eq,nullptr,"[NCUI1]S|1|19|22|0|7|2|13|0|Test",0,false,false);
    assert(SpellLevelHook(spells[0],nullptr,2)==2 && InspectionSpellLevelHook(spells[0],nullptr,2)==255);
    assert(InspectionSpellLevelHook(spells[0],nullptr,13)==2);
#ifdef NIGHTCAP_SPELL_MENU_BASELINE
    (void)started; (void)reenter; OriginalFrame(window,nullptr);
    std::cout << "Cached native label after valid snapshot and frame: " << labels[0]
        << "; direct gem level: " << unsigned(SpellLevelHook(spells[0],nullptr,2)) << '\n';
    assert(labels[0]=="255 - Elementalkin: Water" && rebuilds==1);
    std::cerr << "RED: expected 02 - Elementalkin: Water and order20,17,2 after snapshot; native cache still255,255,20\n";
    return 1;
#else
    original_spell_menu_frame=reinterpret_cast<SpellMenuFrame>(&OriginalFrame);
    rebuild_spell_menu=native_builder; current_spell_profile=reinterpret_cast<CurrentSpellProfile>(&CurrentProfile);
    const auto frame=reinterpret_cast<SpellMenuFrame>(&SpellMenuFrameHook);
    reenter=true; assert(frame(window)==73); reenter=false;
    assert(rebuilds==2 && frames==2 && !spell_menu_dirty);
    assert((labels==std::vector<std::string>{"20 - Greater Healing","17 - Summon Waterstone","02 - Elementalkin: Water"}));
    for(unsigned i=0;i<1000;++i) assert(frame(window)==73);
    assert(rebuilds==2);
    for(const char* message:{"[NCUI1]S|1|19|22|0|7|2|13|0|Test","[NCUI1]S|bad","[NCUI1]A|1|19|22|0|7|123|4"})
        ChatHook(eq,nullptr,message,0,false,false);
    assert(frame(window)==73 && rebuilds==2);
    ChatHook(eq,nullptr,"[NCUI1]S|2|19|22|0|7|2|13|0|Test",0,false,false);
    *reinterpret_cast<uint32_t*>(player+0x148)=8; assert(frame(window)==73 && rebuilds==2 && spell_menu_dirty);
    *reinterpret_cast<uint32_t*>(player+0x148)=7;
    for(unsigned offset:{0x91FC84u,0x9D261Cu,0xA646B0u,0x11D391Cu}) {
        auto slot=reinterpret_cast<void**>(host+offset); auto saved=*slot; *slot=nullptr;
        assert(frame(window)==73 && rebuilds==2 && spell_menu_dirty); *slot=saved;
    }
    profile_result=nullptr; assert(frame(window)==73 && rebuilds==2 && spell_menu_dirty); profile_result=profile;
    profile_result=reinterpret_cast<void*>(1); assert(frame(window)==73 && rebuilds==2 && spell_menu_dirty); profile_result=profile;
    *reinterpret_cast<void**>(character+8)=nullptr; assert(frame(window)==73 && rebuilds==2 && spell_menu_dirty);
    *reinterpret_cast<void**>(character+8)=reinterpret_cast<void*>(1); assert(frame(window)==73 && rebuilds==2 && spell_menu_dirty);
    *reinterpret_cast<void**>(character+8)=vbtable;
    profile[0x3374]=3; assert(frame(window)==73 && rebuilds==2 && spell_menu_dirty); profile[0x3374]=2;
    assert(frame(window)==73 && rebuilds==3);
    // Authoritative book removal and class release must not restore lost access.
    book[0]=-1; book[1]=-1;
    ChatHook(eq,nullptr,"[NCUI1]S|3|19|22|0|7|2|0|0|Test",0,false,false);
    assert(frame(window)==73 && rebuilds==4 && labels==std::vector<std::string>{"20 - Greater Healing"});
    assert(SpellLevelHook(spells[0],nullptr,2)==255 && InspectionSpellLevelHook(spells[0],nullptr,13)==2);
    StateHook(eq,nullptr,1); *reinterpret_cast<int*>(eq+0x5C8)=1;
    assert(frame(window)==73 && rebuilds==4 && spell_menu_dirty);
    *reinterpret_cast<int*>(eq+0x5C8)=5; assert(frame(window)==73 && rebuilds==4 && spell_menu_dirty);
    ChatHook(eq,nullptr,"[NCUI1]S|4|19|22|0|7|2|13|0|Test",0,false,false);
    book[0]=315; assert(frame(window)==73 && rebuilds==5 && labels.back()=="02 - Elementalkin: Water");
    ChatHook(eq,nullptr,"[NCUI1]S|5|19|22|0|7|2|13|0|Test",0,false,false);
    const auto frames_before_failure=frames; mutation_fault=true;
    ExpectMutationFailure(frame,window); mutation_fault=false;
    assert(rebuilds==6 && frames==frames_before_failure); // Native mutation faults are not swallowed.
    ChatHook(eq,nullptr,"[NCUI1]S|6|19|22|0|7|2|13|0|Test",0,false,false);
    assert(frame(window)==73 && rebuilds==7 && labels.back()=="02 - Elementalkin: Water");
    VerifyInstallGuardsAndFrameABI(host,window);
    VirtualFree(reinterpret_cast<void*>(native_builder),0,MEM_RELEASE);
    VirtualFree(reinterpret_cast<void*>(native_order),0,MEM_RELEASE); VirtualFree(host,0,MEM_RELEASE);
    std::cout << "Exact native720-slot menu builder, cached labels, ordering and deferred frame lifecycle passed; "
        << GetTickCount64()-started << " ms\n";
    return 0;
#endif
}
