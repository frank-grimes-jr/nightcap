#pragma once
#include "../../server-mods/code/common/bazaar_panel_protocol.h"

namespace nightcap {
class BazaarPanelState {
	using Snapshot=NightcapBazaarPanel::Snapshot;
	Snapshot current_,pending_;
	uint32_t spawn_=0,request_=0,count_=0;
	std::string name_;
	bool ready_=false,staging_=false,failed_=false,quote_=false,message_=false;
	void Reject(){ready_=staging_=false;failed_=true;pending_={};}
public:
	void Clear(){*this=BazaarPanelState{};}
	void Context(uint32_t spawn,const std::string &name){if(spawn!=spawn_||name!=name_){Clear();spawn_=spawn;name_=name;}}
	void BeginRequest(uint32_t request){request_=request;ready_=staging_=failed_=quote_=message_=false;pending_={};count_=0;}
	bool Ready()const{return ready_;}
	bool Failed()const{return failed_;}
	const Snapshot &Current()const{return current_;}
	bool Consume(std::string_view text){
		using namespace NightcapBazaarPanel;
		if(text.substr(0,7)!="[NCBZ1]")return false;
		std::vector<std::string_view> f;uint32_t request=0;
		if(!NightcapLoot::Fields(text,f)||f.size()<2||!NightcapLoot::Number(f[1],request)){Reject();return true;}
		if(!request_||request!=request_||failed_)return true;
		auto u32=[&](size_t i,uint32_t &n){return i<f.size()&&NightcapLoot::Number(f[i],n);};
		auto decode=[&](size_t i,std::string &s,size_t max=63){return i<f.size()&&NightcapLoot::Unhex(f[i],s,max);};
		auto row=[&](size_t i,Listing &r){return u32(i,r.item)&&u32(i+1,r.quantity)&&u32(i+2,r.price)&&decode(i+3,r.name);};
		auto valid=[](const Listing &r){return r.item&&r.quantity&&r.quantity<=32766&&r.price&&r.price%1000==0&&uint64_t(r.price)*r.quantity<=UINT32_MAX;};
		if(f[0]=="[NCBZ1]B"){
			uint32_t enabled=0;
			if(staging_||ready_||f.size()!=9||!u32(2,pending_.spawn)||!decode(3,pending_.name)||!u32(4,enabled)||enabled>1||
				!u32(5,pending_.page)||!u32(6,pending_.total)||pending_.total>MaxListings||!u32(7,count_)||count_>PageSize||
				!Unsigned(f[8],pending_.credit)||pending_.credit>INT64_MAX||!spawn_||pending_.spawn!=spawn_||pending_.name!=name_||
				pending_.page>((pending_.total?pending_.total:1)-1)/PageSize||count_!=(std::min)(PageSize,pending_.total-pending_.page*PageSize)){
				Reject();return true;
			}
			pending_.request=request;pending_.enabled=enabled!=0;staging_=true;return true;
		}
		if(!staging_){Reject();return true;}
		if(f[0]=="[NCBZ1]Q"){
			if(quote_||f.size()!=7||!row(3,pending_.quote.item)){Reject();return true;}
			if(f[2]!="-"){
				if(!Nonce(f[2])||!valid(pending_.quote.item)){Reject();return true;}
				pending_.quote.nonce=std::string(f[2]);
			}else if(pending_.quote.item.item||pending_.quote.item.quantity||pending_.quote.item.price){Reject();return true;}
			quote_=true;
		}else if(f[0]=="[NCBZ1]R"){
			Listing r;
			if(f.size()!=7||!u32(2,r.id)||!r.id||!row(3,r)||!valid(r)||pending_.rows.size()>=count_){Reject();return true;}
			for(const auto &old:pending_.rows)if(old.id==r.id){Reject();return true;}
			pending_.rows.push_back(std::move(r));
		}else if(f[0]=="[NCBZ1]M"){
			if(message_||f.size()!=3||!decode(2,pending_.message,140)){Reject();return true;}message_=true;
		}else if(f[0]=="[NCBZ1]E"){
			uint32_t count=0;
			if(f.size()!=3||!u32(2,count)||count!=count_||pending_.rows.size()!=count_||!quote_||!message_){Reject();return true;}
			current_=std::move(pending_);ready_=true;staging_=false;
		}else Reject();
		return true;
	}
};
}
