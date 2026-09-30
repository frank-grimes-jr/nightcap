// Exact production currency function bodies; fake database/clients/packets.
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include "common/advanced_loot_policy.h"
#include "zone/advanced_loot_currency.h"
using uint32=uint32_t;
void check(bool ok,const char *message) { if(!ok)throw std::runtime_error(message); }
namespace fmt {
inline std::string format(std::string text){return text;}
template<class T,class... Rest> std::string format(std::string text,const T &value,const Rest &...rest) {
	const auto at=text.find("{}"); check(at!=std::string::npos,"fixture format");std::ostringstream out;out<<value;
	text.replace(at,2,out.str());return format(text,rest...);
}
}
using Wallet=std::array<uint32,4>;
struct Result {
	bool success=true;std::vector<std::vector<std::string>> rows;size_t affected=1;
	bool Success()const{return success;}size_t RowCount()const{return rows.size();}size_t RowsAffected()const{return affected;}
	struct Row { const std::vector<std::string>* values;const char* operator[](size_t i){return values->at(i).c_str();} };
	Row begin()const{return {&rows.at(0)};}
};
struct Database {
	std::vector<std::string> queries;std::map<uint32,Wallet> wallets;bool active=false,committed=false,wrong_engine=false;
	int fail=0,throw_at=0;
	Result QueryDatabase(const std::string &sql,bool retry) {
		check(!retry,"transaction retry enabled");queries.push_back(sql);Result result;
		if(queries.size()==static_cast<size_t>(throw_at))throw std::runtime_error("injected database exception");
		if(queries.size()==static_cast<size_t>(fail)){result.success=false;return result;}
		if(sql.find("information_schema.TABLES")!=std::string::npos)result.rows={{wrong_engine?"1":"2"}};
		else if(sql.find("information_schema.TRIGGERS")!=std::string::npos)result.rows={{"0"}};
		else if(sql=="SELECT @@in_transaction")result.rows={{active?"1":"0"}};
		else if(sql=="START TRANSACTION")active=true;
		else if(sql=="ROLLBACK")active=false;
		else if(sql=="COMMIT"){active=false;committed=true;}
		else if(sql.find("FOR UPDATE")!=std::string::npos){
			const auto id=static_cast<uint32>(std::stoul(sql.substr(sql.find("id=")+3)));
			if(wallets.count(id)){std::vector<std::string> row;for(auto n:wallets.at(id))row.push_back(std::to_string(n));result.rows.push_back(row);}
		}
		return result;
	}
} database;
struct Client;
struct Mob { Client *client=nullptr;bool IsClient()const{return client!=nullptr;}Client* CastToClient(){return client;} };
struct Group { std::vector<Mob*> members; };
struct Raid { struct Member { bool is_bot=false;Client *member=nullptr; };std::vector<Member> members; };
namespace Chat { constexpr int MoneySplit=1; }
namespace Strings { std::string Money(uint32,uint32,uint32,uint32){return "coins";} }
struct Client : Mob {
	struct Profile { uint32 copper=10,silver=20,gold=30,platinum=40; } profile;
	uint32 id;bool connected=true,loaded=true,quarantined=false;unsigned packets=0;Group *group=nullptr;Raid *raid=nullptr;
	explicit Client(uint32 character):id(character){client=this;}
	bool Connected()const{return connected;}bool ClientDataLoaded()const{return loaded;}uint32 CharacterID()const{return id;}
	uint32 GetCopper()const{return profile.copper;}uint32 GetSilver()const{return profile.silver;}
	uint32 GetGold()const{return profile.gold;}uint32 GetPlatinum()const{return profile.platinum;}
	Profile& GetPP(){return profile;}Group* GetGroup(){return group;}Raid* GetRaid(){return raid;}
	void SendMoneyUpdate(){check(database.committed,"money packet preceded commit");++packets;}
	void RecalcWeight(){}void Message(int,const char*,const char*){}void CommonBreakInvisible(){}
	uint64_t GetCarriedMoney(){return 0;}void QuarantineItemTransfer(const char*){quarantined=true;loaded=false;}
};
struct Corpse {
	Wallet coins{7,3,2,5};bool accessible=true;unsigned clears=0;std::string id="11111111-1111-1111-1111-111111111111";
	bool AdvancedLootAccessible(Client*c,bool=false,bool=false){return accessible&&c&&c->Connected()&&c->ClientDataLoaded();}
	uint32 GetCopper(){return coins[0];}uint32 GetSilver(){return coins[1];}uint32 GetGold(){return coins[2];}uint32 GetPlatinum(){return coins[3];}
	std::string GetEntityVariable(const char*){return id;}void SetEntityVariable(const char*,const std::string &value){id=value;}
	void RemoveCash(){coins={};++clears;}bool IsEmpty(){return coins==Wallet{};}void ResetDecayTimer(){}
};
struct QueryServ {};
namespace PlayerEvent { constexpr int SPLIT_MONEY=1;struct SplitMoneyEvent {uint32 copper,silver,gold,platinum;uint64_t player_money_balance;}; }
struct PlayerEventLogs {static PlayerEventLogs* Instance(){static PlayerEventLogs logs;return &logs;}bool IsEventEnabled(int){return false;} };
#define RecordPlayerEventLogWithClient(...) ((void)0)
namespace NightcapLoot {
enum class ClaimStatus {Available,Claimed,Unavailable};
ClaimStatus claim=ClaimStatus::Available;
ClaimStatus ReadClaim(const std::string&){return claim;}
std::string NewDropID(){return "11111111-1111-1111-1111-111111111111";}
}
// ACTUAL_TRANSLATION_UNIT

static Wallet Cash(Client &c){return {c.GetCopper(),c.GetSilver(),c.GetGold(),c.GetPlatinum()};}
static void Saved(Client &c){database.wallets[c.id]=Cash(c);}
int main(){try{
	using namespace NightcapLoot;
	Client a(77),b(88);Group group{{&a,&b}};a.group=&group;Corpse corpse;Saved(a);Saved(b);
	check(TakeCoins(&corpse,&a,true)==TransferResult::Delivered,"split declined");
	check(Cash(a)==Wallet{14,22,31,43}&&Cash(b)==Wallet{13,21,31,42},"split or remainders incorrect");
	check(a.packets==1&&b.packets==1&&corpse.clears==1,"split publication incorrect");
	const auto queries=database.queries;
	for(size_t step=1;step<=queries.size();++step){
		database={};database.fail=static_cast<int>(step);Client x(77),y(88);Group pair{{&x,&y}};x.group=&pair;Corpse drop;Saved(x);Saved(y);
		const auto result=TakeCoins(&drop,&x,true);
		check(result==(queries[step-1]=="COMMIT"?TransferResult::Uncertain:TransferResult::Declined),"failure status incorrect");
		check(Cash(x)==Wallet{10,20,30,40}&&Cash(y)==Wallet{10,20,30,40}&&!x.packets&&!y.packets&&!drop.clears,"failure published coin");
		check(x.quarantined==(result==TransferResult::Uncertain)&&y.quarantined==x.quarantined,"participants quarantine mismatch");
	}
	// Exceptions inside the transaction conservatively quarantine every recipient.
	for(size_t step=3;step<=queries.size();++step){
		database={};database.throw_at=static_cast<int>(step);Client x(77),y(88);Group pair{{&x,&y}};x.group=&pair;Corpse drop;Saved(x);Saved(y);
		check(TakeCoins(&drop,&x,true)==TransferResult::Uncertain&&x.quarantined&&y.quarantined,"exception escaped transfer quarantine");
		check(!x.packets&&!y.packets&&!drop.clears,"exception published coin");
	}
	database={};Client solo(77);Corpse single;Saved(solo);
	check(TakeCoins(&single,&solo,false)==TransferResult::Delivered&&Cash(solo)==Wallet{17,23,32,45},"solo coins wrong");
	database={};Client owner(77),offline(88),bot(99),member(100);offline.connected=false;
	Raid raid{{{false,&owner},{false,&offline},{true,&bot},{false,&member}}};owner.raid=&raid;Corpse raid_drop;Saved(owner);Saved(member);
	check(TakeCoins(&raid_drop,&owner,true)==TransferResult::Delivered&&member.packets==1&&!offline.packets&&!bot.packets,"raid eligibility wrong");
	database={};Client stale(77);Corpse old;Saved(stale);database.wallets[77][0]++;
	check(TakeCoins(&old,&stale,false)==TransferResult::Declined&&!stale.packets&&!old.clears,"stale wallet overwritten");
	database={};Client overflow(77);overflow.profile.platinum=INT32_MAX;Corpse excess;Saved(overflow);
	check(TakeCoins(&excess,&overflow,false)==TransferResult::Declined&&!excess.clears,"wallet overflow accepted");
	database={};claim=ClaimStatus::Claimed;Client replay(77);Corpse ghost;
	check(TakeCoins(&ghost,&replay,false)==TransferResult::Delivered&&ghost.clears==1&&database.queries.empty()&&!replay.packets,"receipt replay paid again");
	claim=ClaimStatus::Unavailable;Corpse unavailable;
	check(TakeCoins(&unavailable,&replay,false)==TransferResult::Declined&&!unavailable.clears,"unavailable claim lost coin");
	std::cout<<"PASS: production currency split/remainders, solo/raid eligibility, every query failure, transaction exceptions, stale/overflow wallets and receipt replay\n";
}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}}
