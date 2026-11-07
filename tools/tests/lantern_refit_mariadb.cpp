// Runs only against the generated disposable schema, on one real connection.
#include "common/last_lantern_inventory.h"
#include <mysql.h>
#include <cassert>
#include <cstdlib>
#include <iostream>
using namespace NightcapLantern;
using namespace NightcapBazaar;
int main() {
	const std::string schema=std::getenv("LANTERN_QA_DB");
	assert(schema.rfind("nightcap_lantern_qa_",0)==0 && schema.size()==32);
	MYSQL *db=mysql_init(nullptr);
	if (!mysql_real_connect(db,std::getenv("LANTERN_QA_HOST"),std::getenv("LANTERN_QA_USER"),std::getenv("LANTERN_QA_PASSWORD"),schema.c_str(),3306,nullptr,0)) { std::cerr<<"Synthetic connection failed"; return 1; }
	auto raw=[&](const std::string &sql) {
		Reply reply;
		if (mysql_real_query(db,sql.data(),sql.size())) { return reply; }
		reply.ok=true; reply.affected=mysql_affected_rows(db); reply.id=mysql_insert_id(db);
		if (auto result=mysql_store_result(db)) {
			while (auto row=mysql_fetch_row(result)) {
				Row values; auto sizes=mysql_fetch_lengths(result);
				for (unsigned i=0;i<mysql_num_fields(result);++i) { values.emplace_back(row[i] ? std::string(row[i],sizes[i]) : ""); }
				reply.rows.push_back(std::move(values));
			} mysql_free_result(result);
		} return reply;
	};
	auto must=[&](const std::string &sql) { auto r=raw(sql); if (!r.ok) { std::cerr<<"Synthetic SQL failed: "<<sql.substr(0,150); std::exit(2); } return r; };
	must("UPDATE nightcap_lantern_control SET enabled=1 WHERE id=1");
	for (unsigned t=9500;t<=9515;++t) { must("INSERT INTO completed_tasks(charid,completedtime,taskid,activityid) VALUES(7,100,"+std::to_string(t)+",-1)"); }
	const std::string initial="INSERT INTO inventory(character_id,slot_id,item_id,charges,color,augment_one,augment_two,augment_three,augment_four,augment_five,augment_six,instnodrop,custom_data,ornament_icon,ornament_idfile,ornament_hero_model,guid) VALUES(7,19,964000,1,123456,100,101,102,103,104,105,1,'route^lantern',22,23,24,777)";
	const std::string uuid="11111111-1111-1111-1111-111111111111";
	must("INSERT INTO nightcap_lantern_slots VALUES(7,0,964000,'"+uuid+"')"); must(initial);
	auto request=[&](const std::string &operation) {
		RefitRequest r; r.character=7; r.level=50; r.classes=1; r.request_id=operation; r.supported_slots={19};
		r.before=must("SELECT "+SelectColumns()+" FROM inventory WHERE character_id=7 AND slot_id=19").rows.at(0);
		r.after=r.before; r.after[2]="964024"; return r;
	};
	const auto original=must("SELECT "+SelectColumns()+" FROM inventory WHERE character_id=7").rows;
	bool injected=false;
	auto fail_owner=[&](const std::string &sql) { if(sql.rfind("UPDATE nightcap_lantern_slots",0)==0) { injected=true; return Reply{}; } return raw(sql); };
	assert(Refit(fail_owner,request("22222222-2222-2222-2222-222222222222"))==Status::Rejected && injected);
	assert(must("SELECT "+SelectColumns()+" FROM inventory WHERE character_id=7").rows==original);
	assert(must("SELECT COUNT(*) FROM nightcap_lantern_refits").rows==Rows{{"0"}});
	// A different player's legitimate recoverable corpse cannot block this refit.
	must("INSERT INTO character_corpses(id,charid,charname) VALUES(990001,8,'SyntheticOther')");
	must("INSERT INTO character_corpse_items(corpse_id,equip_slot,item_id) VALUES(990001,19,964000)");
	const std::string committed="33333333-3333-3333-3333-333333333333";
	assert(Refit(raw,request(committed))==Status::Committed);
	auto expected=original; expected[0][2]="964024";
	assert(must("SELECT "+SelectColumns()+" FROM inventory WHERE character_id=7").rows==expected);
	assert(must("SELECT input_id,output_id FROM nightcap_lantern_refits").rows==Rows({{"964000","964024"}}));
	assert(Refit(raw,request(committed))==Status::Rejected);
	// Restore only synthetic fixture inputs, then execute COMMIT but lose its acknowledgement.
	must("DELETE FROM inventory WHERE character_id=7"); must(initial);
	must("UPDATE nightcap_lantern_slots SET item_id=964000 WHERE character_id=7");
	bool ambiguous=false;
	auto lose_commit=[&](const std::string &sql) { auto r=raw(sql); if(sql=="COMMIT") { ambiguous=true; return Reply{}; } return r; };
	assert(Refit(lose_commit,request("44444444-4444-4444-4444-444444444444"))==Status::Uncertain && ambiguous);
	assert(must("SELECT "+SelectColumns()+" FROM inventory WHERE character_id=7").rows==expected);
	assert(must("SELECT COUNT(*) FROM nightcap_lantern_refits").rows==Rows{{"2"}});
	assert(Refit(raw,request("55555555-5555-5555-5555-555555555555"))==Status::Rejected);
	mysql_close(db);
	std::cout<<"PASS: actual MariaDB atomic refit, complete metadata/GUID preservation, injected rollback, unrelated corpse, replay refusal and ambiguous committed acknowledgement\n";
}
