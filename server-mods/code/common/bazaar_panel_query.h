#pragma once
#include "bazaar_escrow.h"
#include "bazaar_panel_protocol.h"

namespace NightcapBazaarPanel {
// Use the escrow's global serialization row for one coherent owner-only view.
// This path writes nothing and ends with ROLLBACK, including on read failures.
inline NightcapBazaar::Status ReadSeller(const NightcapBazaar::Query &query,uint32_t character,uint32_t page,uint32_t cursor_slot,Snapshot &out) {
	using namespace NightcapBazaar;
	out={};Snapshot pending;bool started=false;
	auto finish=[&](Status status){
		if(started){try{if(!query("ROLLBACK").ok)status=Status::Uncertain;}catch(...){status=Status::Uncertain;}started=false;}
		if(status==Status::Committed){out=std::move(pending);}return status;
	};
	try{
		if(!character||!cursor_slot||page>12||!Ready(query))return Status::Rejected;
		auto active=query("SELECT @@in_transaction");
		if(!active.ok||active.rows!=Rows{{"0"}})return Status::Uncertain;
		started=true;if(!query("START TRANSACTION").ok)return finish(Status::Uncertain);
		auto state=query("SELECT enabled FROM nightcap_bazaar_state WHERE id=1 AND version=1 FOR UPDATE");
		if(!state.ok||state.rows.size()!=1||state.rows[0].size()!=1||(state.rows[0][0]!="0"&&state.rows[0][0]!="1"))return finish(Status::Rejected);
		pending.enabled=state.rows[0][0]=="1";
		const auto who=std::to_string(character);
		auto count=query("SELECT COUNT(*) FROM nightcap_bazaar_listings WHERE seller_id="+who+" AND status='active'");
		if(!count.ok||count.rows.size()!=1||count.rows[0].size()!=1)return finish(Status::Rejected);
		const auto total=Number(count.rows[0][0]);if(total>MaxListings)return finish(Status::Rejected);
		pending.total=static_cast<uint32_t>(total);pending.page=(std::min)(page,(pending.total?pending.total-1:0)/PageSize);
		auto credits=query("SELECT copper FROM nightcap_bazaar_credits WHERE character_id="+who);
		if(!credits.ok||credits.rows.size()>1)return finish(Status::Rejected);
		if(!credits.rows.empty()){
			if(credits.rows[0].size()!=1)return finish(Status::Rejected);
			pending.credit=Number(credits.rows[0][0]);if(pending.credit>MaxCredit)return finish(Status::Rejected);
		}
		auto rows=query("SELECT l.id,i.item_id,l.remaining,l.unit_price FROM nightcap_bazaar_listings l JOIN nightcap_bazaar_items i ON i.listing_id=l.id AND i.slot_id="+std::to_string(cursor_slot)+" WHERE l.seller_id="+who+" AND l.status='active' ORDER BY l.id LIMIT "+std::to_string(PageSize)+" OFFSET "+std::to_string(pending.page*PageSize));
		if(!rows.ok||rows.rows.size()!=(std::min)(PageSize,pending.total-pending.page*PageSize))return finish(Status::Rejected);
		for(const auto &r:rows.rows){
			if(r.size()!=4)return finish(Status::Rejected);
			uint64_t id=Number(r[0]),item=Number(r[1]),quantity=Number(r[2]),price=Number(r[3]);
			if(!id||id>UINT32_MAX||!item||item>UINT32_MAX||!quantity||quantity>32766||!price||price>UINT32_MAX||price*quantity>UINT32_MAX)return finish(Status::Rejected);
			pending.rows.push_back({static_cast<uint32_t>(id),static_cast<uint32_t>(item),static_cast<uint32_t>(quantity),static_cast<uint32_t>(price),{}});
		}
		return finish(Status::Committed);
	}catch(...){return finish(Status::Rejected);}
}
}
