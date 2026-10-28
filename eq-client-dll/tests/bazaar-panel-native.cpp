#include <windows.h>
#include <cassert>
#include <cstring>
#include <iostream>
#include <map>
#include <array>
#include "../src/patch_catalog.h"
#include "../src/ui_hooks.h"
using namespace nightcap::client_ui;
struct Block {alignas(4) std::array<BYTE,0x240> bytes{};};
static std::map<std::string,Block> children;
static std::map<void *,std::string> text;
static std::vector<std::string> requests;
static unsigned frames=0,notifies=0,destroys=0;
static void *expected_window=nullptr;
static EqString *__fastcall Assign(EqString *self,void *,const char *value){self->rep=const_cast<char *>(value);return self;}
static void *__fastcall Child(void *self,void *,const EqString *id){assert(self==expected_window);auto found=children.find(static_cast<const char *>(id->rep));return found==children.end()?nullptr:found->second.bytes.data();}
static void __fastcall SetText(void *self,void *,const EqString *value){text[self]=static_cast<const char *>(value->rep);}
static int __fastcall Frame(void *self,void *){assert(self==expected_window);++frames;return 73;}
static int __fastcall Notify(void *self,void *,void *,uint32_t,void *){assert(self==expected_window);++notifies;return 91;}
static void *__fastcall Destroy(void *self,void *,unsigned flags){assert(flags==1);++destroys;return self;}
static void __fastcall Send(void *,void *,int channel,const char *,const char *request,int){assert(channel==8);requests.emplace_back(request);}
static BOOL WINAPI DenyProtect(LPVOID,SIZE_T,DWORD,PDWORD){return FALSE;}
static BOOL WINAPI DenyFlush(HANDLE,LPCVOID,SIZE_T){return FALSE;}
static void Jump(BYTE *where,void *target){DWORD old=0;assert(VirtualProtect(where,16,PAGE_EXECUTE_READWRITE,&old));where[0]=0xE9;const int32_t offset=int32_t(reinterpret_cast<BYTE *>(target)-(where+5));memcpy(where+1,&offset,4);assert(FlushInstructionCache(GetCurrentProcess(),where,5));}
int main(){
 _set_abort_behavior(0,_CALL_REPORTFAULT);
 // Exact pointer guards must honor image relocation and never adopt other patches.
 for(uint32_t image:{0x400000u,0xda0000u,0x200000u}){
  auto site=static_cast<uint32_t *>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));assert(site);
  *site=image+0x2336f0;
  assert(!PatchBazaarSlot(reinterpret_cast<uintptr_t>(site),kExpectedBazaarFrameSlot,image+1,0x1234));
  assert(!PatchBazaarSlot(reinterpret_cast<uintptr_t>(site),kExpectedBazaarFrameSlot,image,0x1234,&DenyProtect));assert(*site==image+0x2336f0);
  assert(!PatchBazaarSlot(reinterpret_cast<uintptr_t>(site),kExpectedBazaarFrameSlot,image,0x1234,&VirtualProtect,&DenyFlush));assert(*site==image+0x2336f0);
  assert(PatchBazaarSlot(reinterpret_cast<uintptr_t>(site),kExpectedBazaarFrameSlot,image,0x1234));assert(*site==0x1234);
  assert(!PatchBazaarSlot(reinterpret_cast<uintptr_t>(site),kExpectedBazaarFrameSlot,image,0x5678));VirtualFree(site,0,MEM_RELEASE);
 }
 auto host=static_cast<BYTE *>(VirtualAlloc(nullptr,0xA68000,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));assert(host);base=reinterpret_cast<uintptr_t>(host);
 Block window;alignas(4) BYTE eq[0x600]={},player[0x150]={};expected_window=window.bytes.data();window.bytes[0x196]=1;
 *reinterpret_cast<void **>(host+0xa67ccc)=eq;*reinterpret_cast<void **>(host+0x9d2630)=player;*reinterpret_cast<void **>(host+0x9d261c)=player;*reinterpret_cast<void **>(host+0x9d25ac)=player;
 *reinterpret_cast<int *>(eq+0x5c8)=5;*reinterpret_cast<uint32_t *>(player+0x148)=7;memcpy(player+0xa4,"Seller",7);
 Jump(host+kUIStringAssignRva,reinterpret_cast<void *>(&Assign));Jump(host+kUIChildRva,reinterpret_cast<void *>(&Child));
 void *table[80]={};table[0x124/4]=reinterpret_cast<void *>(&SetText);
 for(const char *name:{"SellPage","Price","Post","ConfirmPost","Dismiss","Balance","Collect","Preview","Status","Page","Previous","Next","Cancel","Refresh"})children[std::string("NCBZ_")+name];
 for(unsigned i=0;i<8;++i)children["NCBZ_Row"+std::to_string(i)];
 for(auto &pair:children){*reinterpret_cast<void ***>(pair.second.bytes.data())=table;pair.second.bytes[0x196]=1;}
 alignas(4) BYTE price[96]={};*reinterpret_cast<uint32_t *>(price+4)=40;*reinterpret_cast<uint32_t *>(price+8)=1;memcpy(price+0x14,"1",2);*reinterpret_cast<void **>(children["NCBZ_Price"].bytes.data()+0x1ec)=price;
 send_request=reinterpret_cast<SendRequest>(&Send);original_bazaar_frame=reinterpret_cast<BazaarFrame>(&Frame);original_bazaar_notify=reinterpret_cast<InventoryNotify>(&Notify);original_bazaar_destroy=reinterpret_cast<BazaarDestroy>(&Destroy);
 bazaar_panel=nightcap::BazaarPanelController{};bazaar_panel.Bind(&ExecuteUIRequest);
 const auto frame=reinterpret_cast<BazaarFrame>(&BazaarFrameHook);const auto notify=reinterpret_cast<InventoryNotify>(&BazaarNotifyHook);
 assert(frame(expected_window)==73&&frames==1&&requests.back()=="#bazaar ui 1 view 0 0");
 assert(notify(expected_window,eq,1,nullptr)==91&&notifies==1); // stock sender passes through
 assert(notify(expected_window,children["NCBZ_Price"].bytes.data(),14,nullptr)==1&&notifies==1);
 assert(notify(expected_window,children["NCBZ_Price"].bytes.data(),6,nullptr)==1&&notifies==1);
 NightcapBazaarPanel::Snapshot s;s.request=1;s.spawn=7;s.name="Seller";s.enabled=true;s.message="Ready";
 for(const auto &m:NightcapBazaarPanel::Encode(s))bazaar_panel.Consume(m,GetTickCount64()-500);
 assert(frame(expected_window)==73&&frames==2&&bazaar_panel.CanPost());
 assert(notify(expected_window,children["NCBZ_Post"].bytes.data(),3,nullptr)==1&&requests.size()==1); // right click cannot post
 assert(notify(expected_window,children["NCBZ_Post"].bytes.data(),1,nullptr)==1&&requests.back()=="#bazaar ui 2 post 1 0");
 assert(notify(expected_window,children["NCBZ_Post"].bytes.data(),1,nullptr)==1&&requests.size()==2); // busy double-click
 char output[33]={};assert(BazaarPrice(expected_window,output)&&!strcmp(output,"1"));
 // Native CEditWnd can retain UTF16 even for ordinary whole-platinum digits.
 *reinterpret_cast<uint32_t *>(price+12)=1;assert(BazaarPrice(expected_window,output)&&!strcmp(output,"1"));
 *reinterpret_cast<uint16_t *>(price+0x14)=0x0100;assert(!BazaarPrice(expected_window,output));
 *reinterpret_cast<uint16_t *>(price+0x14)='1';*reinterpret_cast<uint32_t *>(price+4)=3;assert(!BazaarPrice(expected_window,output));
 *reinterpret_cast<uint32_t *>(price+4)=40;*reinterpret_cast<uint16_t *>(price+0x16)='2';assert(!BazaarPrice(expected_window,output));
 *reinterpret_cast<uint16_t *>(price+0x16)=0;*reinterpret_cast<uint32_t *>(price+12)=0;
 *reinterpret_cast<uint32_t *>(price+8)=33;assert(!BazaarPrice(expected_window,output));*reinterpret_cast<uint32_t *>(price+8)=1;
 // Full-length reads require room for the terminator in the native byte capacity.
 for(uint32_t encoding:{0u,1u}){
  const uint32_t stride=encoding+1;*reinterpret_cast<uint32_t *>(price+12)=encoding;
  *reinterpret_cast<uint32_t *>(price+8)=32;
  memset(price+0x14,0,66);for(unsigned i=0;i<32;++i)price[0x14+i*stride]='1';
  *reinterpret_cast<uint32_t *>(price+4)=33*stride;assert(BazaarPrice(expected_window,output)&&strlen(output)==32);
  *reinterpret_cast<uint32_t *>(price+4)=33*stride-1;assert(!BazaarPrice(expected_window,output));
 }
 memset(price,0,sizeof(price));*reinterpret_cast<uint32_t *>(price+8)=1;price[0x14]='1';
 assert(!BazaarPrice(expected_window,output));*reinterpret_cast<uint32_t *>(price+4)=40;
 // An unreadable price must produce visible feedback, never a silent click or request.
 s.request=2;for(const auto &m:NightcapBazaarPanel::Encode(s))bazaar_panel.Consume(m,GetTickCount64()-500);
 frame(expected_window);assert(bazaar_panel.CanPost());
 const auto before_bad_price=requests.size();*reinterpret_cast<uint32_t *>(price+12)=99;
 notify(expected_window,children["NCBZ_Post"].bytes.data(),1,nullptr);
 assert(requests.size()==before_bad_price);assert(bazaar_panel.Feedback().find("price")!=std::string::npos);
 // A valid UTF16 price must reach the real notify/controller request path.
 *reinterpret_cast<uint32_t *>(price+12)=1;
 notify(expected_window,children["NCBZ_Post"].bytes.data(),1,nullptr);
 assert(requests.size()==before_bad_price+1&&requests.back()=="#bazaar ui 3 post 1 0");
 // A failed confirmation read invalidates an existing quote without sending it.
 s.request=3;s.quote={"abcd-1234",{0,1001,1,1000,"Dagger"}};
 for(const auto &m:NightcapBazaarPanel::Encode(s))bazaar_panel.Consume(m,GetTickCount64()-500);
 frame(expected_window);assert(bazaar_panel.HasQuote());
 const auto before_bad_confirm=requests.size();*reinterpret_cast<uint32_t *>(price+12)=99;
 notify(expected_window,children["NCBZ_ConfirmPost"].bytes.data(),1,nullptr);
 assert(requests.size()==before_bad_confirm&&!bazaar_panel.HasQuote());
 *reinterpret_cast<uint32_t *>(price+12)=0;
 assert(bazaar_panel.Post("1"));
 // A character change before the next frame still invalidates the clicked state.
 *reinterpret_cast<uint32_t *>(player+0x148)=8;memcpy(player+0xa4,"Buyer",6);
 const auto before_switch=requests.size();notify(expected_window,children["NCBZ_Collect"].bytes.data(),1,nullptr);assert(requests.size()==before_switch&&!bazaar_panel.Ready());
 const auto count=requests.size();children["NCBZ_SellPage"].bytes[0x196]=0;assert(frame(expected_window)==73&&!bazaar_panel.Opened());assert(requests.size()==count);
 children["NCBZ_SellPage"].bytes[0x196]=1;children.erase("NCBZ_Cancel");assert(frame(expected_window)==73&&!bazaar_panel.Opened());
 assert(reinterpret_cast<BazaarDestroy>(&BazaarDestroyHook)(expected_window,1)==expected_window&&destroys==1);
 base=0;VirtualFree(host,0,MEM_RELEASE);std::cout<<"Bazaar native hook, relocation, input and lifecycle tests passed\n";
}
