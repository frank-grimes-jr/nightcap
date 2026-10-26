#include <cassert>
#include <iostream>
#include "../src/bazaar_panel_controller.h"
using namespace NightcapBazaarPanel;
static std::vector<std::string> sent;
static bool Send(const std::string &text){sent.push_back(text);return true;}
static uint64_t clock_ms=1000;
static void Deliver(nightcap::BazaarPanelController &ui,const Snapshot &s){
 for(const auto &m:Encode(s))assert(ui.Consume(m,clock_ms));
 if(s.name=="Seller"&&s.spawn==7&&s.request!=7){assert(!ui.Ready());assert(!ui.Refresh()&&!ui.Collect()&&!ui.Post("1"));clock_ms+=300;ui.Pulse(clock_ms,7,"Seller",true);}
}
static void ControllerTests(){
 nightcap::BazaarPanelController ui;ui.Bind(&Send);ui.Pulse(1000,7,"Seller",true);
 assert(sent.back()=="#bazaar ui 1 view 0 0" && ui.Busy());
 Snapshot s;s.request=1;s.spawn=7;s.name="Seller";s.enabled=true;s.credit=1234;s.total=1;s.rows.push_back({55,1001,2,1000,"Dagger"});s.message="Ready";
 Deliver(ui,s);assert(ui.Ready()&&ui.CanPost()&&ui.CanCollect());
 assert(!ui.Post("0")&&!ui.Post("4294968")&&!ui.Post("1;quit"));assert(sent.size()==1);
 assert(ui.Post("1"));assert(sent.back()=="#bazaar ui 2 post 1 0");assert(!ui.Post("1")&&!ui.Collect());
 s.request=2;s.quote={"abcd-1234",{0,1001,2,1000,"Dagger"}};Deliver(ui,s);assert(ui.HasQuote());
 assert(!ui.ConfirmPost("2")&&!ui.HasQuote());assert(ui.Post("1"));s.request=3;Deliver(ui,s);
 assert(ui.ConfirmPost("1"));assert(sent.back()=="#bazaar ui 4 confirm abcd-1234 0");
 auto size=sent.size();clock_ms=10000;ui.Pulse(clock_ms,7,"Seller",true);assert(!ui.Ready());assert(sent.size()==size);assert(!ui.ConfirmPost("1"));
 assert(ui.Refresh());assert(sent.back()=="#bazaar ui 5 view 0 0");s.request=5;s.quote={};Deliver(ui,s);
 ui.Select(0);assert(ui.Cancel()&&ui.Cancelling());assert(sent.size()==size+1);assert(ui.Cancel());assert(sent.back()=="#bazaar ui 6 cancel 55 0");
 s.request=6;s.rows.clear();s.total=0;Deliver(ui,s);assert(!ui.Selected());assert(ui.Collect());assert(sent.back()=="#bazaar ui 7 collect 0 0");
 ui.Pulse(11000,8,"Buyer",true);assert(sent.back()=="#bazaar ui 8 view 0 0");s.request=7;Deliver(ui,s);assert(!ui.Ready());
 ui.Pulse(12000,8,"Buyer",false);assert(!ui.Opened());ui.Pulse(13000,8,"Buyer",true);assert(sent.back()=="#bazaar ui 9 view 0 0");
}
static void RapidTabTests(){
 nightcap::BazaarPanelController ui;ui.Bind(&Send);sent.clear();
 ui.Pulse(1000,7,"Seller",true);assert(sent.size()==1);
 ui.Pulse(1050,7,"Seller",false);ui.Pulse(1100,7,"Seller",true);assert(sent.size()==1);
 ui.Pulse(1299,7,"Seller",true);assert(sent.size()==1);
 ui.Pulse(1300,7,"Seller",true);assert(sent.size()==2&&sent.back()=="#bazaar ui 2 view 0 0");
 Snapshot s;s.request=2;s.spawn=7;s.name="Seller";s.enabled=true;s.message="Ready";
 for(const auto &m:Encode(s))ui.Consume(m,1400);
 ui.Pulse(1450,7,"Seller",false);ui.Pulse(1500,7,"Seller",true);assert(sent.size()==2);
 ui.Pulse(1699,7,"Seller",true);assert(sent.size()==2);
 ui.Pulse(1700,7,"Seller",true);assert(sent.size()==3&&sent.back()=="#bazaar ui 3 view 0 0");
}
int main() {
 ControllerTests();RapidTabTests();
 Snapshot s; s.request=1; s.spawn=7; s.name="Seller";s.enabled=true;s.total=1;s.credit=1234;
 s.rows.push_back({55,1001,2,1000,"Dagger"});s.message="Ready";
 nightcap::BazaarPanelState state;state.Context(7,"Seller");state.BeginRequest(1);
 auto messages=Encode(s);for(size_t i=0;i+1<messages.size();++i){assert(state.Consume(messages[i]));assert(!state.Ready());}
 assert(state.Consume(messages.back()) && state.Ready());assert(state.Current().rows[0].id==55);assert(state.Current().credit==1234);
 state.BeginRequest(2);for(auto &m:messages)state.Consume(m);assert(!state.Ready());
 s.request=2;messages=Encode(s);state.Consume(messages[0]);state.Consume(messages[0]);assert(!state.Ready());
 for(size_t i=1;i<messages.size();++i)state.Consume(messages[i]);assert(!state.Ready());
 state.BeginRequest(3);s.request=3;messages=Encode(s);state.Context(8,"Buyer");for(auto &m:messages)state.Consume(m);assert(!state.Ready());
 uint64_t n=0;assert(!Unsigned("18446744073709551616",n));assert(!Unsigned("-1",n));assert(!Unsigned("1;quit",n));assert(Unsigned("9223372036854775807",n));
 std::cout<<"bazaar protocol/state tests passed\n";
}
