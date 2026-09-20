// Hosts the production transaction body and injects every database failure.
#include <array>
#include <cstdint>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using uint32=uint32_t; using uint64=uint64_t; using int16=int16_t;
namespace EQ { namespace invslot { constexpr int slotCursor=33; }
namespace invbag { constexpr int CURSOR_BAG_BEGIN=6010,CURSOR_BAG_END=6209; } }
namespace Strings { uint32 ToUnsignedInt(const char *v) { return std::stoul(v); } }
namespace fmt {
std::string format(std::string s) { return s; }
template<class T,class... R> std::string format(std::string s,const T &v,const R&... rest) {
	std::ostringstream out; out<<v; auto at=s.find("{}");
	if(at==std::string::npos)throw std::runtime_error("bad format fixture");
	s.replace(at,2,out.str());return format(s,rest...);
}
}
struct Reply {
	bool ok=true;size_t rows=0,changed=1;
	bool Success()const{return ok;}size_t RowCount()const{return rows;}size_t RowsAffected()const{return changed;}
	struct Iter { const char *operator[](size_t)const{return "0";} };
	Iter begin()const{return {};}
};
struct FakeDB {
	std::vector<std::string> queries;size_t fail=0,empty=0;bool selling=false,rollback_fail=false,cursor_busy=false;
	Reply QueryDatabase(const std::string &q,bool retry) {
		if(retry)throw std::runtime_error("mutation retry enabled");
		queries.push_back(q);Reply r;
		if(queries.size()==fail || (q=="ROLLBACK" && rollback_fail)){r.ok=false;return r;}
		if(q.rfind("SELECT",0)==0)r.rows=1;
		if(q.rfind("SELECT slot_id FROM inventory",0)==0)r.rows=selling||cursor_busy?1:0;
		if(queries.size()==empty){r.rows=0;r.changed=0;}
		return r;
	}
} database;
namespace NightcapMarket {
struct Offer {uint64 epoch;uint32 npc_id,zone_id,item_id,price_cp;std::string kind;};
struct Item {uint32 id,serial,color;int16 charges;};
using Wallet=std::array<uint32,4>;
enum class Result {Rejected,Committed,Uncertain};
bool Ready(){return true;}
// ACTUAL_TRADE
}
void check(bool b,const char *message){if(!b)throw std::runtime_error(message);}
int main(){try{
	using namespace NightcapMarket;
	const Item item{1001,901,0,0};
	const Wallet before{100,0,0,0},after_buy{90,0,0,0},after_sell{110,0,0,0};
	for(bool selling:{false,true}) {
		const Offer offer{1,999500,22,1001,10000,selling?"buy":"sell"};
		database={};database.selling=selling;
		check(Trade(77,offer,0,before,selling?after_sell:after_buy,item)==Result::Committed,"valid trade rejected");
		const auto trace=database.queries;
		check(trace.size()==12 && trace.back()=="COMMIT","unexpected transaction shape");
		for(size_t fail=1;fail<=trace.size();++fail) {
			database={};database.selling=selling;database.fail=fail;
			const auto result=Trade(77,offer,0,before,selling?after_sell:after_buy,item);
			check(result!=Result::Committed,"injected failure committed");
			if(fail==12)check(result==Result::Uncertain,"lost commit acknowledgement was treated as rejection");
			if(fail>2)check(database.queries.back()=="ROLLBACK","failed transaction not rolled back");
		}
		for(size_t empty:{3,4,5,6,8,9,10,11}) {
			database={};database.selling=selling;database.empty=empty;
			check(Trade(77,offer,0,before,selling?after_sell:after_buy,item)==Result::Rejected,"stale CAS accepted");
		}
		database={};database.selling=selling;database.fail=9;database.rollback_fail=true;
		check(Trade(77,offer,0,before,selling?after_sell:after_buy,item)==Result::Uncertain,"rollback failure not quarantined");
		database={};database.selling=selling;database.empty=selling?7:0;database.cursor_busy=!selling;
		check(Trade(77,offer,0,before,selling?after_sell:after_buy,item)==Result::Rejected,"stale cursor state accepted");
		for(const auto &q:trace)std::cout<<(selling?"SELL:":"BUY:")<<q<<'\n';
	}
	database={};
	check(Trade(77,{1,999500,22,1001,10000,"sell"},0,before,before,item)==Result::Rejected,"wrong wallet delta accepted");
	check(database.queries.empty(),"invalid wallet reached DB");
	std::cout<<"Native market controls passed: 24 database failures, 16 stale predicates, rollback failure and money conservation\n";
	return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
