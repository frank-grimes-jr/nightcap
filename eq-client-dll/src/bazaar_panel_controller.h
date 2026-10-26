#pragma once
#include "bazaar_panel_state.h"

namespace nightcap {
// Presentation state only. Requests use authoritative native server actions.
class BazaarPanelController {
	using Send=bool (*)(const std::string &);
	BazaarPanelState state_;
	Send send_=nullptr;
	uint32_t sequence_=0,selected_=0,cancel_=0,spawn_=0;
	uint64_t now_=0,sent_=0,next_refresh_=0,quote_until_=0,next_action_=0;
	std::string name_,verb_,feedback_;
	bool busy_=false,open_=false,quote_ready_=false,initial_refresh_=false;
	bool Submit(const std::string &verb,const std::string &value,uint32_t page) {
		if(busy_||!spawn_||now_<next_action_||sequence_==UINT32_MAX)return false;
		++sequence_;state_.BeginRequest(sequence_);cancel_=0;quote_ready_=false;feedback_.clear();
		const auto command="#bazaar ui "+std::to_string(sequence_)+" "+verb+" "+value+" "+std::to_string(page);
		busy_=true;sent_=now_;next_action_=now_+300;verb_=verb;next_refresh_=now_+10000;
		if(!send_||!send_(command)){busy_=false;feedback_="Could not send. Click Refresh.";return false;}
		return true;
	}
public:
	void Bind(Send send){send_=send;}
	const NightcapBazaarPanel::Snapshot &Current()const{return state_.Current();}
	bool Ready()const{return open_&&!busy_&&now_>=next_action_&&state_.Ready();}
	bool Busy()const{return busy_;}
	bool CanRefresh()const{return open_&&!busy_&&now_>=next_action_;}
	bool Opened()const{return open_;}
	bool CanPost()const{return Ready()&&Current().enabled;}
	bool CanCollect()const{return Ready()&&Current().credit!=0;}
	bool HasQuote()const{return CanPost()&&quote_ready_&&now_<quote_until_&&!Current().quote.nonce.empty();}
	bool Cancelling()const{return Ready()&&cancel_!=0&&cancel_==selected_;}
	uint32_t SelectedID()const{return selected_;}
	const NightcapBazaarPanel::Listing *Selected()const{
		if(!Ready())return nullptr;
		for(const auto &r:Current().rows)if(r.id==selected_)return &r;
		return nullptr;
	}
	std::string Feedback()const{
		if(!feedback_.empty())return feedback_;
		if(busy_)return "Waiting for the market...";
		return state_.Ready()?Current().message:"Click Refresh to load your listings.";
	}
	void Close(){open_=busy_=quote_ready_=initial_refresh_=false;cancel_=selected_=0;state_.Clear();feedback_.clear();next_refresh_=0;}
	void Pulse(uint64_t now,uint32_t spawn,const std::string &name,bool visible){
		now_=now;
		if(spawn!=spawn_||name!=name_){Close();spawn_=spawn;name_=name;}
		state_.Context(spawn_,name_);
		if(!visible||!spawn_){if(open_)Close();return;}
		if(!open_)initial_refresh_=true;open_=true;
		if(busy_&&now_-sent_>=8000){busy_=false;state_.BeginRequest(0);quote_ready_=false;feedback_="No confirmed reply. Refresh to check the result; do not repeat the action.";}
		if(quote_ready_&&now_>=quote_until_){quote_ready_=false;feedback_="Posting quote expired. Click Post Item for a new preview.";}
		if(initial_refresh_&&!busy_&&now_>=next_action_)Refresh();
		else if(Ready()&&!quote_ready_&&!cancel_&&now_>=next_refresh_)Refresh();
	}
	bool Refresh(){if(!open_||!Submit("view","0",state_.Ready()?Current().page:0))return false;initial_refresh_=false;return true;}
	bool Consume(std::string_view message,uint64_t received_at){
		now_=received_at;
		if(message.substr(0,7)!="[NCBZ1]")return false;
		if(!open_||!busy_)return true;
		state_.Consume(message);
		if(state_.Failed()){busy_=false;feedback_="Market reply was incomplete. Click Refresh.";}
		else if(state_.Ready()){
			busy_=false;cancel_=0;next_action_=now_+300;
			quote_ready_=verb_=="post"&&!Current().quote.nonce.empty();quote_until_=now_+60000;
			bool found=false;for(const auto &row:Current().rows)if(row.id==selected_)found=true;
			if(!found)selected_=0;
		}
		return true;
	}
	bool Post(std::string_view price){
		uint64_t n=0;
		if(!CanPost())return false;
		if(!NightcapBazaarPanel::Unsigned(price,n)||!n||n>UINT32_MAX/1000){quote_ready_=false;feedback_="Enter a whole-platinum price from 1 to 4294967 per item.";return false;}
		return Submit("post",std::to_string(n),Current().page);
	}
	bool ConfirmPost(std::string_view price){
		uint64_t n=0;
		if(!HasQuote())return false;
		if(!NightcapBazaarPanel::Unsigned(price,n)||n!=Current().quote.item.price/1000){quote_ready_=false;feedback_="Price changed. Click Post Item for a new preview.";return false;}
		return Submit("confirm",Current().quote.nonce,Current().page);
	}
	void Dismiss(){quote_ready_=false;cancel_=0;feedback_.clear();}
	void Select(size_t index){if(!Ready()||index>=Current().rows.size())return;selected_=Current().rows[index].id;cancel_=0;quote_ready_=false;feedback_.clear();}
	bool Cancel(){
		const auto row=Selected();if(!row)return false;
		if(cancel_!=row->id){cancel_=row->id;quote_ready_=false;feedback_="Cancel "+row->name+" x"+std::to_string(row->quantity)+"? Clear your cursor, then click Confirm Cancel.";return true;}
		return Submit("cancel",std::to_string(row->id),Current().page);
	}
	bool Collect(){return CanCollect()&&Submit("collect","0",Current().page);}
	bool Page(bool next){
		if(!Ready())return false;
		const auto page=Current().page;
		if(next?(page+1)*NightcapBazaarPanel::PageSize>=Current().total:page==0)return false;
		selected_=0;return Submit("view","0",next?page+1:page-1);
	}
};
}
