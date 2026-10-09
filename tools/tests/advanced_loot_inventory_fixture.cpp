// Host the unmodified production inventory translation unit with dependency fakes.
// This covers placement and transaction ordering, not native packet serialization.
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include "ADVANCED_LOOT_POLICY_PATH"
#include "common/zone_hunt_catalog.h"
#include "common/zone_hunt_policy.h"
using uint8=uint8_t; using uint16=uint16_t; using uint32=uint32_t; using uint64=uint64_t; using int16=int16_t;
void check(bool value,const char *message) { if(!value) throw std::runtime_error(message); }
struct InventoryRepository {
	struct Inventory {
		uint32 character_id=0,slot_id=0,item_id=0; int16 charges=0; uint32 color=0;
		uint32 augment_one=0,augment_two=0,augment_three=0,augment_four=0,augment_five=0,augment_six=0;
		uint8 instnodrop=0; std::string custom_data; uint32 ornament_icon=0,ornament_idfile=0; int ornament_hero_model=0; uint32 guid=0;
	};
	static std::vector<std::string> Columns() { return {"character_id","slot_id","item_id","charges","color","augment_one","augment_two","augment_three","augment_four","augment_five","augment_six","instnodrop","custom_data","ornament_icon","ornament_idfile","ornament_hero_model","guid"}; }
	static std::string ColumnsRaw() { std::string result; for(auto &column:Columns()) { if(!result.empty())result+=","; result+=column; } return result; }
};
namespace Strings {
std::string ToLower(std::string value) { return value; }
std::string Implode(const std::string &separator,const std::vector<std::string> &values) { std::string result; bool first=true; for(const auto &value:values) { if(!first)result+=separator; first=false; result+=value; } return result; }
}
namespace fmt {
inline std::string format(std::string text) { return text; }
template<class T,class... Rest> std::string format(std::string text,const T &value,const Rest &...rest) {
	const auto at=text.find("{}"); if(at==std::string::npos)throw std::runtime_error("fixture formatting");
	std::ostringstream stream;stream<<value;text.replace(at,2,stream.str());return format(text,rest...);
}
}
namespace EQ {
namespace invaug { constexpr uint8 SOCKET_COUNT=6; }
namespace invslot { constexpr int16 EQUIPMENT_BEGIN=0,EQUIPMENT_END=22,GENERAL_BEGIN=23,GENERAL_END=32,slotCursor=33,SLOT_INVALID=-1; }
namespace invbag { constexpr uint8 SLOT_COUNT=10; constexpr int16 CURSOR_BAG_BEGIN=351,CURSOR_BAG_END=360; }
struct ItemData { uint32 ID=1001; int16 StackSize=20; uint8 BagSlots=0; int Size=1,BagSize=10; };
struct ItemInstance {
	ItemData data; InventoryRepository::Inventory row; int16 charges=1; bool stackable=false,evolving=false,equipped=false;
	uint64 evolve_id=0; std::map<uint8,std::shared_ptr<ItemInstance>> contents;
	ItemInstance() { row.item_id=data.ID; row.guid=901; }
	ItemInstance(const ItemData *item,int16 count):data(*item),charges(count) { static uint32 next=902;row.item_id=data.ID;row.guid=next++; }
	const ItemData *GetItem()const{return &data;}
	const ItemInstance *GetItem(uint8 slot)const{auto i=contents.find(slot);return i==contents.end()?nullptr:i->second.get();}
	uint32 GetID()const{return row.item_id;} int16 GetCharges()const{return charges;} void SetCharges(int value){charges=static_cast<int16>(value);}
	uint32 GetColor()const{return row.color;}
	uint32 GetAugmentItemID(int i)const{return std::array<uint32,6>{row.augment_one,row.augment_two,row.augment_three,row.augment_four,row.augment_five,row.augment_six}[i];}
	bool IsAttuned()const{return row.instnodrop!=0;} std::string GetCustomDataString()const{return row.custom_data;}
	void SetAttuned(bool b){row.instnodrop=b;} bool IsScaling()const{return false;} bool IsClassCommon()const{return !IsClassBag();}
	uint32 GetOrnamentationIcon()const{return row.ornament_icon;} uint32 GetOrnamentationIDFile()const{return row.ornament_idfile;}
	int GetOrnamentHeroModel()const{return row.ornament_hero_model;} uint32 GetSerialNumber()const{return row.guid;} void SetSerialNumber(uint32 id){row.guid=id;}
	bool IsClassBag()const{return data.BagSlots>0;} bool IsStackable()const{return stackable;} ItemInstance *Clone()const{return new ItemInstance(*this);}
	void SetEvolveEquipped(bool value){equipped=value;} bool IsEvolving()const{return evolving;} uint64 GetEvolveUniqueID()const{return evolve_id;}
	uint64 GetEvolveCurrentAmount()const{return 10;} void SetEvolveUniqueID(uint64 value){evolve_id=value;}
	void SetEvolveCharID(uint32){} void SetEvolveItemID(uint32){} void SetEvolveFinalItemID(uint32){} void CalculateEvolveProgression(){}
};
struct InventoryProfile {
	struct Lookup { uint64 PossessionsBitmask=(uint64{1}<<23)|(uint64{1}<<24)|(uint64{1}<<33); } lookup;
	std::map<int16,std::shared_ptr<ItemInstance>> items; unsigned puts=0; bool fail_put=false;
	const Lookup *GetLookup()const{return &lookup;}
	bool CursorEmpty()const{return items.count(invslot::slotCursor)==0;}
	const ItemInstance *GetItem(int16 slot)const{auto i=items.find(slot);return i==items.end()?nullptr:i->second.get();}
	int16 PutItem(int16 slot,const ItemInstance &item){++puts;if(fail_put)return -1;items[slot]=std::shared_ptr<ItemInstance>(item.Clone());return slot;}
	static int16 CalcSlotId(int16 parent,uint8 index){return static_cast<int16>(251+(parent-23)*10+index);}
	static int16 CalcSlotId(int16 child){return static_cast<int16>(23+(child-251)/10);}
	static bool CanItemFitInContainer(const ItemData *item,const ItemData *bag){return !item->BagSlots && item->Size<=bag->BagSize;}
};
namespace Util { struct UUID { static UUID Generate(){return {};} std::string ToString()const{return "11111111-1111-1111-1111-111111111111";} }; }
}
struct EvolvingItemsManager { static EvolvingItemsManager *Instance(){static EvolvingItemsManager manager;return &manager;} uint32 GetFinalItemID(const EQ::ItemInstance &item){return item.GetID()+1;} };
using Cells=std::vector<std::vector<std::string>>;
struct MySQLRequestRow { const std::vector<std::string> *values; const char *operator[](size_t i){return values->at(i).c_str();} };
struct Iterator {
	const Cells *rows;size_t at=0;MySQLRequestRow operator*()const{return {&rows->at(at)};}
	const char *operator[](size_t i)const{return rows->at(at).at(i).c_str();}
	Iterator &operator++(){++at;return *this;}bool operator!=(const Iterator &other)const{return at!=other.at;}
};
struct Result {
	bool success=true;Cells cells;size_t affected=1;
	bool Success()const{return success;}size_t RowCount()const{return cells.size();}size_t RowsAffected()const{return affected;}
	Iterator begin()const{return {&cells,0};}Iterator end()const{return {&cells,cells.size()};}
};
struct ZoneDatabase {
	std::vector<std::string> queries;Cells inventory;int fail=0,throw_at=0,zero_at=0;bool committed=false,active=false,claimed=false,wrong_engine=false,forged=false,rollback_fail=false;
	EQ::ItemInstance *CreateItem(uint32 id,int charges){EQ::ItemData data;data.ID=id;return new EQ::ItemInstance(&data,static_cast<int16>(charges));}
	Result QueryDatabase(const std::string &q,bool retry) {
		check(!retry,"a transaction query enabled retry");queries.push_back(q);Result result;
		if(queries.size()==static_cast<size_t>(throw_at))throw std::runtime_error("injected database exception");
		if(queries.size()==static_cast<size_t>(fail)){result.success=false;return result;}
		if(queries.size()==static_cast<size_t>(zero_at))result.affected=0;
		if(q=="ROLLBACK" && rollback_fail){result.success=false;return result;}
		if(q.rfind("SHOW COLUMNS",0)==0){for(const auto &column:InventoryRepository::Columns())result.cells.push_back({column});}
		else if(q.find("information_schema.TABLES")!=std::string::npos)result.cells={{wrong_engine?"0":q.find("nightcap_zone_hunt_state")!=std::string::npos?"2":"3"}};
		else if(q.find("information_schema.TRIGGERS")!=std::string::npos)result.cells={{"0"}};
		else if(q=="SELECT @@in_transaction")result.cells={{active?"1":"0"}};
		else if(q=="START TRANSACTION")active=true;
		else if(q=="COMMIT"){committed=true;active=false;}
		else if(q=="ROLLBACK")active=false;
		else if(q.find("FROM inventory WHERE")!=std::string::npos)result.cells=inventory;
		else if(q=="SELECT LAST_INSERT_ID()")result.cells={{"12345"}};
		else if(q.rfind("SELECT drop_id",0)==0 && claimed)result.cells={{"11111111-1111-1111-1111-111111111111"}};
		else if(q.rfind("SELECT revision",0)==0)result.cells={{"2026100901"}};
		else if(q.rfind("SELECT request_id",0)==0 && forged)result.cells={{"11111111-1111-1111-1111-111111111111"}};
		return result;
	}
} database;
namespace Chat { constexpr int Red=1; }
constexpr int ItemPacketTrade=1;
struct Client {
	EQ::InventoryProfile inventory;bool quarantined=false;unsigned packets=0,bonuses=0,equip_notifications=0;int16 equip_slot=EQ::invslot::SLOT_INVALID;
	bool Connected()const{return !quarantined;}bool ClientDataLoaded()const{return !quarantined;}uint32 CharacterID()const{return 77;}
	EQ::InventoryProfile &GetInv(){return inventory;}void Message(int,const char*){}
	void QuarantineItemTransfer(const char*){quarantined=true;}
	void SendItemPacket(int16,const EQ::ItemInstance*,int){check(database.committed,"packet preceded acknowledged commit");++packets;}
	void CalcBonuses(){check(database.committed,"bonuses preceded acknowledged commit");++bonuses;}
	bool CheckLoreConflict(const EQ::ItemData*){return false;}
	void DeleteItemInInventory(int16 slot,int,bool update,bool persist){check(database.committed&&!persist,"delete preceded commit or persisted twice");inventory.items.erase(slot);if(update)++packets;}
	int16 FindLootEquipSlot(const EQ::ItemInstance &) { return equip_slot; }
	void NotifyLootEquipped(EQ::ItemInstance &,int16 slot) { check(database.committed&&inventory.GetItem(slot),"equip event preceded committed item install");++equip_notifications; }
};
// ACTUAL_TRANSLATION_UNIT

static const std::string id="11111111-1111-1111-1111-111111111111";
static EQ::ItemInstance Item(bool stack=false,int count=1) {
	EQ::ItemInstance item;item.stackable=stack;item.charges=static_cast<int16>(count);return item;
}
static void SaveRow(int16 slot,const EQ::ItemInstance &item) {
	auto values=NightcapLoot::Values(NightcapLoot::FromItem(77,slot,item));
	values[12]=item.GetCustomDataString();database.inventory.push_back(values);
}
static std::vector<NightcapLoot::ForgeInput> PrepareForge(Client &c) {
	c.inventory.lookup.PossessionsBitmask|=uint64{1}<<25;
	std::vector<NightcapLoot::ForgeInput> inputs;
	for(int16 slot:{23,24,25}) {
		auto item=Item();item.row.item_id=item.data.ID=940024;item.row.guid=900+slot;
		item.SetAttuned(slot==24);c.inventory.items[slot]=std::make_shared<EQ::ItemInstance>(item);
		SaveRow(slot,item);database.inventory.back()[16]=std::to_string(700+slot); // saved GUID differs after login
		inputs.emplace_back(slot,item.GetSerialNumber());
	}
	return inputs;
}
static void TestForge() {
	using namespace NightcapLoot;
	database={};Client c;auto inputs=PrepareForge(c);
	check(ForgeItems(&c,inputs,id)==TransferResult::Delivered,"three-copy forge failed");
	check(c.inventory.items.size()==1&&c.inventory.GetItem(23)->GetID()==940025&&c.inventory.GetItem(23)->IsAttuned(),"forge output/count/binding mismatch");
	check(c.inventory.puts==1&&c.packets==4&&c.bonuses==1,"forge published incorrect inventory updates");
	const auto successful=database.queries;
	check(std::count_if(successful.begin(),successful.end(),[](const auto&q){return q.rfind("DELETE FROM inventory",0)==0;})==3,"did not delete exactly three preimages");
	for(size_t step=1;step<=successful.size();++step) {
		database={};Client attempt;auto copies=PrepareForge(attempt);database.fail=static_cast<int>(step);
		const auto result=ForgeItems(&attempt,copies,id);
		const bool uncertain=successful[step-1]=="COMMIT"||successful[step-1]=="SELECT @@in_transaction"||successful[step-1]=="START TRANSACTION";
		check(result==(uncertain?TransferResult::Uncertain:TransferResult::Declined),"incorrect forge failure classification");
		check(attempt.quarantined==uncertain&&attempt.inventory.items.size()==3&&!attempt.inventory.puts&&!attempt.packets,"forge failure published items or lost quarantine");
	}
	for(size_t step=1;step<=successful.size();++step) {
		database={};Client attempt;auto copies=PrepareForge(attempt);database.throw_at=static_cast<int>(step);
		check(ForgeItems(&attempt,copies,id)==TransferResult::Uncertain&&attempt.quarantined,"forge exception not quarantined");
		check(attempt.inventory.items.size()==3&&!attempt.packets,"exception published forge inventory");
	}
	for(size_t step=1;step<=successful.size();++step) {
		if(successful[step-1].rfind("DELETE ",0)!=0&&successful[step-1].rfind("INSERT ",0)!=0)continue;
		database={};Client attempt;auto copies=PrepareForge(attempt);database.zero_at=static_cast<int>(step);
		check(ForgeItems(&attempt,copies,id)==TransferResult::Declined&&!attempt.packets,"forge ignored affected-row failure");
	}
	database={};Client duplicate;auto copies=PrepareForge(duplicate);copies[2]=copies[1];
	check(ForgeItems(&duplicate,copies,id)==TransferResult::Declined&&database.queries.empty(),"duplicate source consumed");
	database={};Client stale;copies=PrepareForge(stale);database.inventory[1][12]="changed";
	check(ForgeItems(&stale,copies,id)==TransferResult::Declined&&!stale.packets,"stale instance consumed");
	database={};Client stale_quote;copies=PrepareForge(stale_quote);++copies[1].second;
	check(ForgeItems(&stale_quote,copies,id)==TransferResult::Declined&&database.queries.empty(),"stale quote consumed replacement");
	database={};Client payload;copies=PrepareForge(payload);payload.inventory.items[24]->row.augment_one=123;
	check(ForgeItems(&payload,copies,id)==TransferResult::Declined&&database.queries.empty(),"socketed input consumed");
	database={};Client top;copies=PrepareForge(top);top.inventory.items[24]->row.item_id=940027;
	check(ForgeItems(&top,copies,id)==TransferResult::Declined&&database.queries.empty(),"mixed or top-tier input consumed");
	database={};Client replay;copies=PrepareForge(replay);database.forged=true;
	check(ForgeItems(&replay,copies,id)==TransferResult::Declined&&!replay.packets,"request receipt replayed");
	database={};Client rollback;copies=PrepareForge(rollback);database.inventory[0][2]="1";database.rollback_fail=true;
	check(ForgeItems(&rollback,copies,id)==TransferResult::Uncertain&&rollback.quarantined,"failed rollback not quarantined");
	database={};Client broken_publish;copies=PrepareForge(broken_publish);broken_publish.inventory.fail_put=true;
	check(ForgeItems(&broken_publish,copies,id)==TransferResult::Uncertain&&broken_publish.quarantined&&database.committed,"post-commit failure not quarantined");
	for(const auto&q:successful)std::cout<<"FORGE_SQL:"<<q<<"\n";
}
int main() { try {
	using namespace NightcapLoot;
	Client client;auto source=Item();source.row.color=0xff010203;source.row.augment_one=201;source.row.augment_six=206;
	source.row.custom_data="quote'\\line\n^";source.row.ornament_icon=301;source.row.ornament_idfile=302;source.row.ornament_hero_model=-4;
	check(ReceiveItem(&client,source,{id})==TransferResult::Delivered,"ordinary item not delivered");
	check(client.inventory.puts==1 && client.packets==1 && client.bonuses==1,"ordinary item installed more than once");
	check(SameItem(FromItem(77,23,source),FromItem(77,23,*client.inventory.GetItem(23))),"instance metadata changed");
	const auto successful=database.queries;
	for(size_t step=1;step<=successful.size();++step) {
		database={};database.fail=static_cast<int>(step);Client attempt;
		const auto result=ReceiveItem(&attempt,source,{id});
		check(result==(successful[step-1]=="COMMIT"?TransferResult::Uncertain:TransferResult::Declined),"wrong injected-failure result");
		check(attempt.inventory.puts==0 && attempt.packets==0 && attempt.bonuses==0,"failure mutated inventory");
		check(attempt.quarantined==(result==TransferResult::Uncertain),"wrong failure quarantine");
	}
	for(size_t step=1;step<=successful.size();++step) {
		database={};database.throw_at=static_cast<int>(step);Client attempt;
		check(ReceiveItem(&attempt,source,{id})==TransferResult::Uncertain && attempt.quarantined,"exception was not quarantined");
		check(!attempt.inventory.puts && !attempt.packets,"exception published inventory");
	}
	database={};Client full;full.inventory.items[23]=std::make_shared<EQ::ItemInstance>(source);full.inventory.items[24]=std::make_shared<EQ::ItemInstance>(source);
	check(ReceiveItem(&full,source,{id})==TransferResult::Declined && database.queries.empty(),"full bags issued a write");
	database={};Client manual;
	check(ReceiveItem(&manual,source,{id},false,Destination::Cursor)==TransferResult::Delivered&&manual.inventory.GetItem(33)&&!manual.inventory.GetItem(23),"classic manual click did not use cursor");
	database={};Client fallback;fallback.inventory.items[23]=std::make_shared<EQ::ItemInstance>(source);fallback.inventory.items[24]=std::make_shared<EQ::ItemInstance>(source);SaveRow(23,source);SaveRow(24,source);
	check(ReceiveItem(&fallback,source,{id},false,Destination::InventoryOrCursor)==TransferResult::Delivered&&fallback.inventory.GetItem(33),"classic auto pickup lost empty-cursor fallback");
	database={};Client occupied;occupied.inventory.items[33]=std::make_shared<EQ::ItemInstance>(source);
	check(ReceiveItem(&occupied,source,{id},false,Destination::Cursor)==TransferResult::Declined&&database.queries.empty(),"classic cursor item overwritten");
	database={};Client stale_cursor;SaveRow(33,source);
	check(ReceiveItem(&stale_cursor,source,{id},false,Destination::Cursor)==TransferResult::Declined&&!stale_cursor.packets,"saved cursor preimage overwritten");
	database={};Client stale_children;SaveRow(351,source);
	check(ReceiveItem(&stale_children,source,{id},false,Destination::Cursor)==TransferResult::Declined&&!stale_children.packets,"orphan cursor state overwritten");
	database={};Client partial_fallback;auto almost=Item(true,19);partial_fallback.inventory.items[23]=std::make_shared<EQ::ItemInstance>(almost);partial_fallback.inventory.items[24]=std::make_shared<EQ::ItemInstance>(source);SaveRow(23,almost);SaveRow(24,source);
	check(ReceiveItem(&partial_fallback,Item(true,8),{id},false,Destination::InventoryOrCursor)==TransferResult::Delivered&&partial_fallback.inventory.GetItem(23)->GetCharges()==19&&partial_fallback.inventory.GetItem(33)->GetCharges()==8,"cursor fallback retained a partial inventory plan");
	database={};Client cursor_bag;auto filled_bag=Item();filled_bag.data.BagSlots=2;filled_bag.contents[0]=std::make_shared<EQ::ItemInstance>(source);
	check(ReceiveItem(&cursor_bag,filled_bag,{id},false,Destination::Cursor)==TransferResult::Delivered&&cursor_bag.inventory.GetItem(33)&&cursor_bag.inventory.GetItem(351),"cursor bag contents missing");
	database={};Client stacked;auto partial=Item(true,15);stacked.inventory.items[23]=std::make_shared<EQ::ItemInstance>(partial);SaveRow(23,partial);
	check(ReceiveItem(&stacked,Item(true,8),{id})==TransferResult::Delivered,"stack merge failed");
	check(stacked.inventory.GetItem(23)->GetCharges()==20 && stacked.inventory.GetItem(24)->GetCharges()==3,"stack merge lost charges");
	database={};Client split;
	check(ReceiveItem(&split,Item(true,40),{id})==TransferResult::Delivered,"split across empty slots failed");
	check(split.inventory.GetItem(23)->GetCharges()==20 && split.inventory.GetItem(24)->GetCharges()==20 &&
		split.inventory.GetItem(23)->GetSerialNumber()!=split.inventory.GetItem(24)->GetSerialNumber(),"split stacks share a serial or lost charges");
	database={};Client stale;SaveRow(23,source);
	check(ReceiveItem(&stale,source,{id})==TransferResult::Declined && !stale.inventory.puts,"occupied database slot overwritten");
	database={};Client bagged;auto bag=Item();bag.data.BagSlots=2;bagged.inventory.items[23]=std::make_shared<EQ::ItemInstance>(bag);bagged.inventory.items[24]=std::make_shared<EQ::ItemInstance>(source);SaveRow(23,bag);SaveRow(24,source);
	check(ReceiveItem(&bagged,source,{id})==TransferResult::Delivered && bagged.inventory.GetItem(251),"compatible bag slot not used");
	database={};Client repair;repair.inventory.fail_put=true;
	check(ReceiveItem(&repair,source,{id})==TransferResult::Uncertain && repair.quarantined && database.committed,"post-commit install failure not quarantined");
	database={};Client evolving;auto evolution=source;evolution.evolving=true;
	check(ReceiveItem(&evolving,evolution,{id})==TransferResult::Delivered && evolving.inventory.GetItem(23)->GetEvolveUniqueID()==12345,"evolving record not installed");
	const auto evolving_queries=database.queries;
	for(size_t step=1;step<=evolving_queries.size();++step) {
		database={};database.fail=static_cast<int>(step);Client attempt;
		const auto result=ReceiveItem(&attempt,evolution,{id});
		check(result==(evolving_queries[step-1]=="COMMIT"?TransferResult::Uncertain:TransferResult::Declined),"wrong evolving failure result");
		check(!attempt.inventory.puts && !attempt.packets,"evolving failure published inventory");
	}
	database={};Client auto_equip;auto_equip.equip_slot=13;
	check(ReceiveItem(&auto_equip,evolution,{id},false,Destination::InventoryOrCursor)==TransferResult::Delivered&&auto_equip.inventory.GetItem(13)&&!auto_equip.inventory.GetItem(23)&&auto_equip.equip_notifications==1,"classic auto-loot did not equip exactly once");
	check(auto_equip.inventory.GetItem(13)->equipped,"evolving equipped flag missing in memory");
	const auto equipped_queries=database.queries;
	check(std::any_of(equipped_queries.begin(),equipped_queries.end(),[](const auto &q){return q.find("VALUES (77,1001,0,1,10,0,1002)")!=std::string::npos;}),"evolving equipped flag missing in database");
	for(size_t step=1;step<=equipped_queries.size();++step) {
		database={};database.fail=static_cast<int>(step);Client attempt;attempt.equip_slot=13;
		check(ReceiveItem(&attempt,evolution,{id},false,Destination::InventoryOrCursor)!=(TransferResult::Delivered),"failed equipment transaction delivered");
		check(!attempt.inventory.puts&&!attempt.packets&&!attempt.equip_notifications,"failed equipment transaction published item or quest event");
	}
	database={};Client advanced;advanced.equip_slot=13;
	check(ReceiveItem(&advanced,source,{id})==TransferResult::Delivered&&advanced.inventory.GetItem(23)&&!advanced.inventory.GetItem(13)&&!advanced.equip_notifications,"advanced loot unexpectedly equipped item");
	database={};Client stale_worn;stale_worn.equip_slot=13;SaveRow(14,source);
	check(ReceiveItem(&stale_worn,source,{id},false,Destination::InventoryOrCursor)==TransferResult::Declined&&!stale_worn.packets&&!stale_worn.equip_notifications,"auto-equip ignored persisted hand preimage");
	database={};Client duplicate;
	check(ReceiveItem(&duplicate,source,{id,id})==TransferResult::Declined && database.queries.empty(),"duplicate physical IDs accepted");
	check(!ValidDropID("wrong") && ValidDropID(id),"drop identity validation failed");
	TestForge();
	for(const auto &query:successful)std::cout<<"SQL:"<<query<<"\n";
	std::cout<<"PASS: actual loot and forge translation unit; inventory preimages, binding, replay, placement and every database failure/exception boundary\n";
	return 0;
} catch(const std::exception &error) { std::cerr<<error.what()<<"\n";return 1; } }
