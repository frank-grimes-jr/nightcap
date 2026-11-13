#include "../src/dllmain.cpp"
#include <cassert>
#include <iostream>
#include <vector>
using namespace nightcap::client_ui;
static std::string label;
static unsigned polls=0,chat_lines=0;
static EqString* __fastcall Assign(EqString* out,void*,const char* text){label=text;out->rep=nullptr;return out;}
static void __fastcall Request(void*,void*,int channel,const char* target,const char* text,int unknown){
 assert(channel==8 && !target && !unknown);if(!strcmp(text,"#nightcapui inventory"))++polls;
}
static void __fastcall Chat(void*,void*,const char*,int,bool,bool){++chat_lines;}
static void __fastcall SetState(void*,void*,int){}
static bool __cdecl Stock(int,EqString*,bool*,unsigned long*){label="stock";return true;}
static void Jump(BYTE* site,void* target){site[0]=0xe9;*reinterpret_cast<int32_t*>(site+1)=static_cast<int32_t>(reinterpret_cast<uintptr_t>(target)-reinterpret_cast<uintptr_t>(site+5));}
int main(){
 auto host=static_cast<BYTE*>(VirtualAlloc(nullptr,0xA68000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));assert(host);
 base=reinterpret_cast<uintptr_t>(host);*reinterpret_cast<void**>(host+0x9D261C)=host;*reinterpret_cast<void**>(host+0x9D25AC)=host;BYTE eq[0x600]={},player[0x150]={};
 *reinterpret_cast<void**>(host+0xA67CCC)=eq;*reinterpret_cast<void**>(host+0x9D2630)=player;
 *reinterpret_cast<int*>(eq+0x5c8)=5;*reinterpret_cast<unsigned*>(player+0x148)=7;memcpy(player+0xa4,"Palwar",7);
 Jump(host+kUIStringAssignRva,reinterpret_cast<void*>(&Assign));send_request=reinterpret_cast<SendRequest>(&Request);
 original_chat=reinterpret_cast<DisplayChat>(&Chat);original_state=reinterpret_cast<SetGameState>(&SetState);original_label=&Stock;
 assert(state.Consume("[NCUI1]S|1|29|39|0|7|1|3|0|Palwar"));
 EqString output{};bool override_color=false;unsigned long color=0;
 assert(LabelHook(10200,&output,&override_color,&color));assert(label=="--" && polls==1 && override_color && color==0xFFAAAAAA);
 LabelHook(10309,&output,&override_color,&color);assert(polls==1 && label=="--");
 NightcapStats::Snapshot s;s.identity={1,29,39,0,7};s.sequence=100;s.values[NightcapStats::ShieldBlock]=16;
 s.values[NightcapStats::HuntBlock]=1;s.values[NightcapStats::Heal]=92;s.values[NightcapStats::HealCap]=780;
 ChatHook(eq,nullptr,NightcapStats::Encode(s).c_str(),0,false,false);assert(chat_lines==0);
 LabelHook(10200,&output,&override_color,&color);assert(label=="16%" && color==0xFF00FF00);
 LabelHook(10309,&output,&override_color,&color);assert(label=="92/780");
 ChatHook(eq,nullptr,"[NCST1]|malformed",0,true,true);assert(chat_lines==0);
 *reinterpret_cast<unsigned*>(player+0x148)=8;
 LabelHook(10200,&output,&override_color,&color);assert(label=="--" && color==0xFFAAAAAA);
 *reinterpret_cast<unsigned*>(player+0x148)=7;
 assert(state.Consume("[NCUI1]S|2|29|39|0|7|1|3|0|Palwar"));
 ChatHook(eq,nullptr,NightcapStats::Encode(s).c_str(),0,false,false);
 LabelHook(10200,&output,&override_color,&color);assert(label=="--");
 s.identity[0]=2;s.sequence=101;ChatHook(eq,nullptr,NightcapStats::Encode(s).c_str(),0,false,false);
 LabelHook(10200,&output,&override_color,&color);assert(label=="16%");
 NightcapInventory::Snapshot inv;inv.identity=s.identity;inv.sequence=101;
 inv.values[NightcapInventory::Mitigation]=916;inv.values[NightcapInventory::Defense]=795;
 inv.values[NightcapInventory::Strength]=434;inv.values[NightcapInventory::StrengthCap]=434;
 inv.values[NightcapInventory::HeroicStrength]=104;
 ChatHook(eq,nullptr,NightcapInventory::Encode(inv).c_str(),0,false,false);assert(chat_lines==0);
 LabelHook(10500,&output,&override_color,&color);assert(label=="916" && color==0xFF00FF00);
 LabelHook(10501,&output,&override_color,&color);assert(label=="795");
 LabelHook(10600,&output,&override_color,&color);assert(label=="434" && color==0xFF00FF00);
 LabelHook(10800,&output,&override_color,&color);assert(label=="/434" && color==0xFFFFFFFF);
 LabelHook(10700,&output,&override_color,&color);assert(label=="+104" && color==0xFFD6B228);
 assert(polls==1); // New and old views share one quiet bounded request.
 ChatHook(eq,nullptr,"[NCIV1]|malformed",0,true,true);assert(chat_lines==0);
 inv.sequence=102;inv.values[NightcapInventory::Defense]=-1;
 ChatHook(eq,nullptr,NightcapInventory::Encode(inv).c_str(),0,false,false);
 LabelHook(10501,&output,&override_color,&color);assert(label=="Auto");
 *reinterpret_cast<unsigned*>(player+0x148)=8;
 LabelHook(10700,&output,&override_color,&color);assert(label=="--" && color==0xFFAAAAAA);
 *reinterpret_cast<unsigned*>(player+0x148)=7;
 LabelHook(123,&output,&override_color,&color);assert(label=="stock");
 ChatHook(eq,nullptr,"ordinary chat",0,false,false);assert(chat_lines==1);
 StateHook(eq,nullptr,3);assert(!equipped_stats.Ready(s.identity,GetTickCount64()) && next_stats_refresh==0);
 assert(!inventory_stats.Ready(inv.identity,GetTickCount64()));
 std::cout<<"PASS: real label/chat/reset hooks, automatic bounded polling, current caps, stale identity and silent frames\n";
}
