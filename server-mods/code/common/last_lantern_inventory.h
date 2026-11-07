#pragma once
#include "last_lantern_policy.h"
#include "bazaar_escrow.h"
#include "item_xp_inventory.h"
#include <set>

namespace NightcapLantern {
using NightcapBazaar::Query;
using NightcapBazaar::Row;
using NightcapBazaar::Status;
struct RefitRequest {
	uint32_t character=0, level=0, classes=0;
	std::string request_id;
	Row before, after; // full native inventory rows; custom_data is hex
	std::vector<uint32_t> supported_slots; // from the native inventory lookup
	Row parent; // native parent bag preimage when the carried source is inside one
};
inline bool UUID(const std::string &value) {
	if (value.size()!=36) { return false; }
	for (size_t i=0;i<value.size();++i) {
		if (i==8 || i==13 || i==18 || i==23) { if (value[i]!='-') { return false; } }
		else if (!((value[i]>='0' && value[i]<='9') || (value[i]>='a' && value[i]<='f'))) { return false; }
	}
	return true;
}
inline void Normalize(Row &row) {
	if (row.size()!=17) { return; }
	for (auto &c:row[12]) { if (c>='a' && c<='f') { c-=32; } }
}
inline std::string HexAudit(const std::string &value) {
	static constexpr char digits[]="0123456789abcdef";
	std::string result; result.reserve(value.size()*2);
	for (unsigned char c:value) { result+=digits[c>>4]; result+=digits[c&15]; }
	return result;
}

// The caller passes a no-retry query on the one native inventory connection.
// No packets, task mutation, item removal or memory writes belong in this engine.
inline Status Refit(const Query &query,RefitRequest request) {
	using namespace NightcapBazaar;
	bool open=false, commit_attempted=false;
	auto reject=[&]() {
		if (open) {
			open=false;
			try { if (!query("ROLLBACK").ok) { return Status::Uncertain; } }
			catch (...) { return Status::Uncertain; }
		}
		return Status::Rejected;
	};
	try {
		Normalize(request.before); Normalize(request.after);
		const auto &before=request.before; const auto &after=request.after;
		if (!request.character || !UUID(request.request_id) || before.size()!=17 || after.size()!=17 ||
			!ValidItem(before,request.character) || !ValidItem(after,request.character)) { return Status::Rejected; }
		if (std::find(request.supported_slots.begin(),request.supported_slots.end(),Number(before[1]))==request.supported_slots.end()) { return Status::Rejected; }
		Normalize(request.parent);
		if (!request.parent.empty() && !ValidItem(request.parent,request.character)) { return Status::Rejected; }
		for (size_t i=0;i<17;++i) {
			// Preserve custom dye, augments, binding, ornaments, custom fields and GUID.
			if (i!=2 && before[i]!=after[i]) { return Status::Rejected; }
		}
		const auto source=Number(before[2]), target=Number(after[2]);
		if (source>UINT32_MAX || target>UINT32_MAX || !IsArmor(unsigned(source)) || !IsArmor(unsigned(target))) { return Status::Rejected; }
		const auto slot=Decode(unsigned(source)).slot;
		const std::string tables="'inventory','nightcap_lantern_control','nightcap_lantern_slots','nightcap_lantern_refits','completed_tasks','sharedbank','guild_bank','character_parcels','character_parcels_containers','character_corpse_items','character_pet_inventory','character_pet_armor','nightcap_bazaar_items','object_contents','trader'";
		const auto engines=query("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN ("+tables+") AND ENGINE='InnoDB'");
		const auto triggers=query("SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE IN ("+tables+")");
		const auto transaction=query("SELECT @@in_transaction,@@autocommit");
		if (!engines.ok || engines.rows!=Rows{{"15"}} || !triggers.ok || triggers.rows!=Rows{{"0"}} ||
			!transaction.ok || transaction.rows!=Rows{{"0","1"}}) { return Status::Rejected; }
		open=true;
		if (!query("START TRANSACTION").ok) { return reject(); }
		const auto gate=query("SELECT revision FROM nightcap_lantern_control WHERE id=1 AND enabled=1 AND revision="+std::to_string(Revision)+" FOR UPDATE");
		if (!gate.ok || gate.rows!=Rows{{std::to_string(Revision)}}) { return reject(); }
		const auto owner=query("SELECT item_id,drop_id FROM nightcap_lantern_slots WHERE character_id="+std::to_string(request.character)+" AND armor_slot="+std::to_string(slot)+" FOR UPDATE");
		if (!owner.ok || owner.rows.size()!=1 || owner.rows[0].size()!=2 || owner.rows[0][0]!=before[2] || !UUID(owner.rows[0][1])) { return reject(); }
		const auto tasks=query("SELECT taskid FROM completed_tasks WHERE charid="+std::to_string(request.character)+" AND activityid=-1 AND taskid BETWEEN 9500 AND 9515 FOR UPDATE");
		if (!tasks.ok) { return reject(); }
		uint16_t completed=0;
		for (const auto &row:tasks.rows) {
			if (row.size()!=1) { return reject(); }
			const auto id=Number(row[0]);
			if (id<FirstTask || id>=FirstTask+TaskCount) { return reject(); }
			completed|=uint16_t(1u<<(id-FirstTask));
		}
		if (!CanRefit(unsigned(source),unsigned(target),request.level,request.classes,completed)) { return reject(); }
		const auto prior=query("SELECT request_id FROM nightcap_lantern_refits WHERE request_id='"+request.request_id+"' FOR UPDATE");
		if (!prior.ok || !prior.rows.empty()) { return reject(); }
		// Personal campaign armor is never legal in these custody channels. Refuse
		// any conflicting row rather than manufacture or refit an ambiguous copy.
		for (const auto *table:{"sharedbank","guild_bank","character_parcels","character_parcels_containers","character_corpse_items","character_pet_inventory","character_pet_armor","nightcap_bazaar_items","object_contents","trader"}) {
			const std::string column=std::string(table)=="object_contents" ? "itemid" : "item_id";
			const auto custody=query("SELECT "+column+" FROM "+table+" WHERE "+column+">="+std::to_string(FirstArmor)+" AND "+column+"<"+std::to_string(FirstArmor+ArmorCount)+" FOR UPDATE");
			if (!custody.ok || !custody.rows.empty()) { return reject(); }
		}
		const auto inventory=query("SELECT "+SelectColumns()+" FROM inventory WHERE character_id="+std::to_string(request.character)+" FOR UPDATE");
		if (!inventory.ok) { return reject(); }
		unsigned owned=0, matching=0, parents=0;
		std::set<std::string> slots;
		Row persisted_before;
		for (auto row:inventory.rows) {
			Normalize(row);
			if (!ValidItem(row,request.character) || !slots.insert(row[1]).second) { return reject(); }
			const auto item_id=Number(row[2]);
			if (item_id<=UINT32_MAX && IsArmor(unsigned(item_id)) && Decode(unsigned(item_id)).slot==slot) { ++owned; }
			if (row[1]==before[1]) {
				for (size_t i=0;i<16;++i) { if (row[i]!=before[i]) { return reject(); } }
				++matching;
				persisted_before=row;
			}
			if (!request.parent.empty() && row[1]==request.parent[1]) {
				for (size_t i=0;i<16;++i) { if (row[i]!=request.parent[i]) { return reject(); } }
				++parents;
			}
		}
		if (owned!=1 || matching!=1 || (!request.parent.empty() && parents!=1)) { return reject(); }
		request.before[16]=request.after[16]=persisted_before[16];
		const auto update=NightcapItemXP::UpdateSQL(before,after);
		if (update.empty()) { return reject(); }
		auto write=query(update+" AND guid="+persisted_before[16]);
		if (!write.ok || write.affected!=1) { return reject(); }
		write=query("UPDATE nightcap_lantern_slots SET item_id="+after[2]+" WHERE character_id="+before[0]+" AND armor_slot="+std::to_string(slot)+" AND item_id="+before[2]);
		if (!write.ok || write.affected!=1) { return reject(); }
		const auto audit=query("INSERT INTO nightcap_lantern_refits(request_id,character_id,armor_slot,input_id,output_id,inventory_before,inventory_after) VALUES ('"+
			request.request_id+"',"+before[0]+","+std::to_string(slot)+","+before[2]+","+after[2]+",X'"+HexAudit(Join(before))+"',X'"+HexAudit(Join(after))+"')");
		if (!audit.ok || audit.affected!=1) { return reject(); }
		commit_attempted=true;
		const auto committed=query("COMMIT");
		if (!committed.ok) { reject(); return Status::Uncertain; }
		open=false; return Status::Committed;
	} catch (...) {
		const auto status=reject();
		return commit_attempted ? Status::Uncertain : status;
	}
}
}
