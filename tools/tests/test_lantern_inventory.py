"""Exercise real campaign refit transaction code with injected storage failures."""
import unittest
import test_free_trade as native


class LanternInventoryTests(unittest.TestCase):
    def test_refit_transaction_and_complete_preimage(self):
        native.FreeTradeTests.compile_run(self, r'''
#include "common/last_lantern_inventory.h"
#include <cassert>
#include <iostream>
using namespace NightcapLantern;
using namespace NightcapBazaar;
struct DB {
 int n=0,fail=0,throw_at=0; bool committed=false,duplicate=false,wrong_owner=false,missing_task=false;
 bool rollback_fail=false,outside=false;
 Rows inventory; std::vector<std::string> trace;
 Reply operator()(const std::string &sql) {
  ++n; trace.push_back(sql);
  if(sql=="ROLLBACK" && rollback_fail)return {};
  if(n==throw_at) throw std::runtime_error("injected");
  if(n==fail) return {};
  Reply r; r.ok=true;r.affected=1;
  if(sql.find("information_schema.TABLES")!=std::string::npos) r.rows={{"16"}};
  else if(sql.find("information_schema.TRIGGERS")!=std::string::npos) r.rows={{"0"}};
  else if(sql.find("@@in_transaction")!=std::string::npos) r.rows={{"0","1"}};
  else if(sql.find("SELECT revision FROM nightcap_lantern_control")!=std::string::npos)r.rows={{std::to_string(Revision)}};
  else if(sql.find("SELECT taskid FROM completed_tasks")!=std::string::npos) {
   for(unsigned i=0;i<16;++i) if(!missing_task || i!=15)r.rows.push_back({std::to_string(9500+i)});
  }
  else if(sql.find("SELECT item_id,drop_id FROM nightcap_lantern_slots")!=std::string::npos)
   r.rows={{wrong_owner ? "964001" : "964000","11111111-1111-1111-1111-111111111111"}};
  else if(sql.find("SELECT request_id FROM nightcap_lantern_refits")!=std::string::npos) {
   if(duplicate) r.rows={{"22222222-2222-2222-2222-222222222222"}};
  }
  else if(sql.find(" FROM inventory WHERE character_id=7 FOR UPDATE")!=std::string::npos)r.rows=inventory;
  else if(sql.find("SELECT item_id FROM sharedbank")!=std::string::npos && outside)r.rows={{"964000"}};
  else if(sql=="COMMIT")committed=true;
  return r;
 }
};
RefitRequest request() {
 RefitRequest r;r.character=7;r.level=50;r.classes=1;
 r.supported_slots={19};
 r.request_id="22222222-2222-2222-2222-222222222222";
 r.before={"7","19","964000","1","123","900","0","0","0","0","0","1","6162","8","9","10","42"};
 r.after=r.before;r.after[2]="964024";return r;
}
int main() {
 const auto req=request();DB good;good.inventory={req.before};
 assert(Refit([&](const std::string&s){return good(s);},req)==Status::Committed);
 assert(good.committed);const int queries=good.n;
 for(int fail=1;fail<=queries;++fail) {
  DB db;db.inventory={req.before};db.fail=fail;
  auto status=Refit([&](const std::string&s){return db(s);},req);
  assert(status!=Status::Committed);
  if(fail==queries)assert(status==Status::Uncertain);
  if(fail==4)assert(db.trace.back()=="ROLLBACK");
 }
 for(int fail=1;fail<=queries;++fail) {
  DB db;db.inventory={req.before};db.throw_at=fail;
  assert(Refit([&](const std::string&s){return db(s);},req)!=Status::Committed);
  if(fail==4)assert(db.trace.back()=="ROLLBACK");
 }
 for(size_t column=0;column<req.before.size();++column) {
  if(column==16)continue; // persisted GUID is intentionally not a runtime identity
  DB db;auto row=req.before;row[column]=column==12 ? "6163" : "99";db.inventory={row};
  assert(Refit([&](const std::string&s){return db(s);},req)==Status::Rejected);
 }
 for(size_t column=0;column<req.after.size();++column) {
  if(column==2 || column==4)continue;
  DB db;db.inventory={req.before};auto changed=req;changed.after[column]=column==12 ? "6163" : "99";
  assert(Refit([&](const std::string&s){return db(s);},changed)==Status::Rejected);
 }
 for(int mode=0;mode<4;++mode) {
  DB db;db.inventory={req.before};
  if(mode==0)db.inventory.push_back(req.before);
  if(mode==1)db.duplicate=true;
  if(mode==2)db.wrong_owner=true;
  if(mode==3)db.missing_task=true;
  assert(Refit([&](const std::string&s){return db(s);},req)==Status::Rejected);
 }
 auto evil=req;evil.request_id="x';DELETE FROM inventory;--";DB db;db.inventory={req.before};
 assert(Refit([&](const std::string&s){return db(s);},evil)==Status::Rejected && db.n==0);
 auto dye=req;dye.after[4]="456";
 assert(Refit([&](const std::string&s){return db(s);},dye)==Status::Rejected); // custom dye must survive
 DB default_dye;default_dye.inventory={req.before};
 auto default_req=req;default_req.after[4]="456";
 default_req.source_default_color=123;default_req.target_default_color=456;
 assert(Refit([&](const std::string&s){return default_dye(s);},default_req)==Status::Committed);
 DB rollback;rollback.inventory={req.before};rollback.fail=5;rollback.rollback_fail=true;
 assert(Refit([&](const std::string&s){return rollback(s);},req)==Status::Uncertain);
 DB outside;outside.inventory={req.before};outside.outside=true;
 assert(Refit([&](const std::string&s){return outside(s);},req)==Status::Rejected);
 auto bank=req;bank.before[1]=bank.after[1]="2000";DB bank_db;bank_db.inventory={bank.before};
 assert(Refit([&](const std::string&s){return bank_db(s);},bank)==Status::Rejected);
 DB changed_guid;auto saved=req.before;saved[16]="999";changed_guid.inventory={saved};
 assert(Refit([&](const std::string&s){return changed_guid(s);},req)==Status::Committed);
 bool actual_audit=false;
 for(const auto& sql:changed_guid.trace)if(sql.find("INSERT INTO nightcap_lantern_refits")==0)
  actual_audit=sql.find(HexAudit(Join(saved)))!=std::string::npos;
 assert(actual_audit);
 std::cout<<"campaign refit failure and preservation controls passed\n";
}
''')


if __name__ == '__main__':
    unittest.main()
