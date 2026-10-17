#include <windows.h>
#include <cassert>
#include <iostream>
#include <vector>
#include "../src/patch_catalog.h"
#include "../src/ui_hooks.h"
using namespace nightcap::client_ui;
static BYTE button[0x200]={};
static BYTE reset_button[0x200]={};
static BYTE rank1[0x90]={},rank2[0x90]={};
static bool affordable=true,raise_native=false;
static unsigned notifications=0;
static std::vector<unsigned> shown;
static EqString* __fastcall Assign(EqString* s,void*,const char* v){s->rep=const_cast<char*>(v);return s;}
static void* __fastcall Child(void*,void*,const EqString* s){
    const auto name=static_cast<const char*>(s->rep);
    return strcmp(name,"NC_AARecommended")==0 ? button : strcmp(name,"ResetFilter")==0 ? reset_button : nullptr;
}
static bool __fastcall Affordable(void*,void*,void*,void*,int,int,int){return affordable;}
static int __fastcall Notify(void*,void*,void*,uint32_t,void*){++notifications;return 7;}
static void Jump(BYTE* site,void* target){
    site[0]=0xE9;const auto offset=static_cast<int32_t>(reinterpret_cast<uintptr_t>(target)-reinterpret_cast<uintptr_t>(site+5));
    memcpy(site+1,&offset,4);
}
static void __fastcall Update(void* self,void*) {
    if(raise_native) RaiseException(0xE0123456,0,0,nullptr);
    shown.clear();
    for(auto rank:{rank1,rank2}) if(AAFilterHook(static_cast<BYTE*>(self)+0x22c,nullptr,rank)) shown.push_back(*reinterpret_cast<unsigned*>(rank));
}
static void ExceptionControl(void* self) {
    bool caught=false;
    __try {CallOriginalAA(self);}
    __except(EXCEPTION_EXECUTE_HANDLER){caught=true;}
    assert(caught && !aa_filter_active);
}
int main(){
    auto host=static_cast<BYTE*>(VirtualAlloc(nullptr,0xA68000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));assert(host);
    base=reinterpret_cast<uintptr_t>(host);
    BYTE eq[0x600]={},player[0x150]={},window[0x300]={};
    *reinterpret_cast<void**>(host+0xA67CCC)=eq;*reinterpret_cast<void**>(host+0x9D2630)=player;
    *reinterpret_cast<int*>(eq+0x5c8)=5;*reinterpret_cast<unsigned*>(player+0x148)=7;memcpy(player+0xa4,"Palwar",7);
    Jump(host+kUIStringAssignRva,reinterpret_cast<void*>(&Assign));Jump(host+kUIChildRva,reinterpret_cast<void*>(&Child));
    // Execute the actual RoF2 filter bytes. Only its two absolute globals are
    // rebased; its native affordability callee is the controlled boundary.
    const BYTE native[]={0x56,0x8b,0x74,0x24,0x08,0x57,0x8b,0xf9,0x85,0xf6,0x0f,0x84,0x81,0x00,0x00,0x00,0x80,0x3f,0x00,0x74,0x1c,0xa1,0x1c,0x26,0xdd,0x00,0x8b,0x0d,0x58,0x03,0xd2,0x00,0x6a,0x00,0x6a,0x00,0x6a,0x00,0x56,0x50,0xe8,0xe3,0xbe,0xe9,0xff,0x84,0xc0,0x74,0x19,0x8b,0x47,0x04,0x48,0x74,0x1a,0x48,0x75,0x1d,0x39,0x46,0x4c,0x7e,0x18,0x8b,0xce,0xe8,0xaa,0x5b,0xe2,0xff,0x85,0xc0,0x75,0x0d,0x5f,0x32,0xc0,0x5e,0xc2,0x04,0x00,0x83,0x7e,0x4c,0x00,0x7e,0xf3,0x8b,0x47,0x0c,0x85,0xc0,0x7e,0x08,0x39,0x86,0x8c,0x00,0x00,0x00,0x75,0xe4,0x8b,0x7f,0x08,0x85,0xff,0x7e,0x08,0x39,0xbe,0x88,0x00,0x00,0x00,0x75,0xd5,0x80,0x7e,0x7c,0x00,0x74,0x16,0x8b,0x36,0x8b,0x0d,0x1c,0x26,0xdd,0x00,0x6a,0x00,0x6a,0x00,0x56,0xe8,0x33,0xa0,0xf7,0xff,0x84,0xc0,0x74,0xb9,0x5f,0xb0,0x01,0x5e,0xc2,0x04,0x00};
    memcpy(host+kUIAAFilterRva,native,sizeof(native));
    for(auto offset:{0x16,0x1c,0x7f}) {
        auto ptr=reinterpret_cast<uint32_t*>(host+kUIAAFilterRva+offset);
        *ptr=static_cast<uint32_t>(base+*ptr-0x400000);
    }
    Jump(host+0xa44c0,reinterpret_cast<void*>(&Affordable));
    original_aa_filter=reinterpret_cast<AAFilter>(host+kUIAAFilterRva);
    original_aa=reinterpret_cast<UpdateAA>(&Update);original_aa_notify=reinterpret_cast<InventoryNotify>(&Notify);
    *reinterpret_cast<unsigned*>(rank1)=100;*reinterpret_cast<unsigned*>(rank2)=200;
    assert(state.Consume("[NCUI1]S|1|42|63|0|7|3|1|7|Palwar"));
    button[0x1e4]=1; CallOriginalAA(window);assert(shown.size()==2); // unavailable is all, not empty
    assert(state.Consume("[NCUI1]B|1|42|63|0|7|1"));assert(state.Consume("[NCUI1]R|1|42|63|0|7|200|1|0|3"));assert(state.Consume("[NCUI1]E|1|42|63|0|7"));
    CallOriginalAA(window);assert(shown==std::vector<unsigned>{200} && !aa_filter_active);
    button[0x1e4]=0;CallOriginalAA(window);assert(shown.size()==2);
    button[0x1e4]=1;window[0x22c]=1;affordable=false;CallOriginalAA(window);assert(shown.empty());
    affordable=true;CallOriginalAA(window);assert(shown==std::vector<unsigned>{200});
    window[0x22c]=0;
    *reinterpret_cast<int*>(window+0x234)=7; // native expansion filter still intersects
    CallOriginalAA(window);assert(shown.empty());*reinterpret_cast<int*>(rank2+0x88)=7;
    CallOriginalAA(window);assert(shown==std::vector<unsigned>{200});
    *reinterpret_cast<int*>(window+0x234)=0;
    assert(AANotifyHook(window,nullptr,button,1,nullptr)==1 && notifications==0);
    assert(AANotifyHook(window,nullptr,reset_button,1,nullptr)==7 && !button[0x1e4] && notifications==1);
    assert(AANotifyHook(window,nullptr,rank1,1,nullptr)==7 && notifications==2);
    button[0x1e4]=1;*reinterpret_cast<unsigned*>(player+0x148)=8;CallOriginalAA(window);assert(shown.size()==2);
    *reinterpret_cast<unsigned*>(player+0x148)=7;raise_native=true;ExceptionControl(window);raise_native=false;
    assert(state.Consume("[NCUI1]S|2|42|63|0|7|3|1|0|Palwar"));CallOriginalAA(window);assert(shown.size()==2);
    assert(state.Consume("[NCUI1]B|2|42|63|0|7|0"));assert(state.Consume("[NCUI1]E|2|42|63|0|7"));CallOriginalAA(window);assert(shown.empty());
    VirtualFree(host,0,MEM_RELEASE);base=0;state.Clear();
    std::cout<<"Native RoF2 filter, controls, affordability, identity and SEH checks passed\n";
}
