// This fixture hosts the actual FromInstance/Predicate/SchemaReady/Transfer bodies.
// It injects a failure at every database call; it does not emulate EQ gameplay.
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using uint8 = uint8_t; using uint32 = uint32_t; using int16 = int16_t;
struct InventoryRepository {
	struct Inventory {
		uint32 character_id=0; int16 slot_id=0; uint32 item_id=0; uint16_t charges=0;
		uint32 color=0, augment_one=0, augment_two=0, augment_three=0, augment_four=0,
			augment_five=0, augment_six=0; uint8 instnodrop=0; std::string custom_data;
		uint32 ornament_icon=0, ornament_idfile=0; int ornament_hero_model=0; uint32 guid=0;
	};
	static std::vector<std::string> Columns() { return {"character_id","slot_id","item_id","charges","color",
		"augment_one","augment_two","augment_three","augment_four","augment_five","augment_six",
		"instnodrop","custom_data","ornament_icon","ornament_idfile","ornament_hero_model","guid"}; }
};
namespace EQ {
namespace invslot { constexpr int16 slotCursor=33; }
namespace invbag { constexpr int16 CURSOR_BAG_BEGIN=6010, CURSOR_BAG_END=6209; }
struct ItemInstance {
	InventoryRepository::Inventory row; int16 charges=0; bool legal=true;
	uint32 GetID() const {return row.item_id;}
	int16 GetCharges() const {return charges;}
	uint32 GetColor() const {return row.color;}
	uint32 GetAugmentItemID(int i) const {return std::array<uint32,6>{row.augment_one,row.augment_two,row.augment_three,row.augment_four,row.augment_five,row.augment_six}[i];}
	bool IsAttuned() const {return row.instnodrop!=0;}
	std::string GetCustomDataString() const {return row.custom_data;}
	uint32 GetOrnamentationIcon() const {return row.ornament_icon;}
	uint32 GetOrnamentationIDFile() const {return row.ornament_idfile;}
	int GetOrnamentHeroModel() const {return row.ornament_hero_model;}
	uint32 GetSerialNumber() const {return row.guid;}
	ItemInstance* Clone() const {return new ItemInstance(*this);}
};
}
namespace Strings {
std::string Implode(const std::string& delimiter,const std::vector<std::string>& parts) {
	std::string out; for (const auto &p:parts) {if (!out.empty())out+=delimiter;out+=p;}return out;
}
uint32 ToUnsignedInt(const char* value) {return static_cast<uint32>(std::stoul(value));}
}
namespace fmt {
inline std::string format(std::string pattern) {return pattern;}
template<class T,class... Rest> std::string format(std::string pattern,T value,Rest... rest) {
	std::ostringstream text;text<<+value;auto at=pattern.find("{}");
	if(at==std::string::npos)throw std::runtime_error("fixture format");
	pattern.replace(at,2,text.str());return format(pattern,rest...);
}
}
using Cells=std::vector<std::vector<std::string>>;
struct View { const std::vector<std::string>* values; const char* operator[](size_t i)const{return values->at(i).c_str();} };
struct Iterator {
	const Cells* rows; size_t at=0;
	View operator*()const{return {&rows->at(at)};}
	const char* operator[](size_t i)const{return rows->at(at).at(i).c_str();}
	Iterator& operator++(){++at;return *this;}
	bool operator!=(const Iterator& other)const{return at!=other.at;}
};
struct Result {
	bool success=true; Cells cells; size_t affected=1;
	bool Success()const{return success;}size_t RowCount()const{return cells.size();}
	size_t RowsAffected()const{return affected;}
	Iterator begin()const{return {&cells,0};}Iterator end()const{return {&cells,cells.size()};}
};
struct FakeDB {
	std::vector<std::string> queries; int fail=0; bool equip=true, stale=false, occupied=false, queue=false;
	Result QueryDatabase(const std::string& q,bool retry) {
		if(retry)throw std::runtime_error("transaction query allowed reconnect/retry");
		queries.push_back(q);Result r;
		if(fail && queries.size()==static_cast<size_t>(fail)){r.success=false;return r;}
		if(q.rfind("SHOW COLUMNS",0)==0){for(const auto& c:InventoryRepository::Columns())r.cells.push_back({c});if(q.find("character_pet_armor")!=std::string::npos)r.cells.push_back({"pet_class"});}
		else if(q.find("information_schema.TABLES")!=std::string::npos)r.cells={{"2"}};
		else if(q.find("information_schema.TRIGGERS")!=std::string::npos || q=="SELECT @@in_transaction")r.cells={{"0"}};
		else if(q.rfind("SELECT slot_id",0)==0){
			bool cursor=q.find("(slot_id=")!=std::string::npos;
			bool target=q.find("WHERE character_id=")!=std::string::npos && !cursor;
			size_t count=cursor ? (equip?1:0)+(queue?1:0) : target ? (equip?0:1)+(occupied?1:0) : (stale?0:1);
			for(size_t i=0;i<count;++i)r.cells.push_back({"33"});
		}
		return r;
	}
} database;
namespace NightcapPetArmor {
using Row=InventoryRepository::Inventory;
constexpr std::array<int16,8> Slots={2,17,7,9,12,18,19,20};
struct Item {Row saved;std::shared_ptr<EQ::ItemInstance> instance;};
bool Allowed(const EQ::ItemInstance* item,uint8 index){return item && item->legal && index<8;}
// ACTUAL_METHODS
}
void check(bool condition,const char* message){if(!condition)throw std::runtime_error(message);}
int main(){try{
	using namespace NightcapPetArmor;
	EQ::ItemInstance cursor;cursor.row={77,33,1001,0,0xff010203,201,202,203,204,205,206,1,"key^quote'\\line\n^",601,602,-4,901};
	Item empty, result;
	check(Transfer(77,13,0,true,&cursor,empty,result),"equip failed");
	check(result.saved.slot_id==2 && result.saved.charges==0 && result.saved.guid==901,"equip lost instance fields");
	check(result.instance.get()!=&cursor,"equip did not clone");
	const auto equipQueries=database.queries;
	check(equipQueries.size()==12,"unexpected transaction call count");
	check(equipQueries[8].find("BINARY COALESCE")!=std::string::npos,"custom data equality is not binary");
	check(equipQueries[9].find("augment_six")!=std::string::npos,"sixth augment missing");
	Item stored=result;stored.instance->row.guid=902; // next session has a fresh serial
	database={};database.equip=false;
	check(Transfer(77,13,0,false,nullptr,stored,result),"remove failed");
	check(result.saved.slot_id==33 && result.saved.guid==902,"fresh session serial not persisted");
	const auto removeQueries=database.queries;
	check(removeQueries[8].find("`guid`=901")!=std::string::npos,"saved serial not used for CAS");
	check(removeQueries[9].find(",902 FROM")!=std::string::npos,"fresh serial missing from destination");
	for(bool equip:{false,true})for(int fail=1;fail<=12;++fail){
		database={};database.equip=equip;database.fail=fail;Item untouched;untouched.saved.guid=9999;
		check(!Transfer(77,13,0,equip,equip?&cursor:nullptr,equip?empty:stored,untouched),"failed query accepted");
		check(untouched.saved.guid==9999 && !untouched.instance,"failed transaction published memory");
		if(fail>=7)check(database.queries.back()=="ROLLBACK","transaction failure omitted rollback");
	}
	for(int control=0;control<3;++control){
		database={};database.stale=control==0;database.occupied=control==1;database.queue=control==2;
		check(!Transfer(77,13,0,true,&cursor,empty,result),"conflicting state accepted");
		check(database.queries.back()=="ROLLBACK","conflict omitted rollback");
		for(const auto& q:database.queries)check(q.rfind("INSERT",0)!=0,"wrote before validating conflict");
	}
	for(int16 charges:{int16(-1),int16(0),int16(7)}){
		database={};cursor.charges=charges;
		check(Transfer(77,13,0,true,&cursor,empty,result),"charges equip failed");
		check(result.saved.charges==(charges<0?32767:charges),"charges encoding changed");
	}
	database={};check(!Transfer(77,13,8,true,&cursor,empty,result),"ninth slot accepted");check(database.queries.empty(),"invalid request reached DB");
	std::cout<<"Native transfer controls passed: 24 injected failures, CAS, occupied slot, cursor queue, 3 charge states, GUID reassignment\n";
	for(const auto& q:equipQueries)std::cout<<"EQUIP:"<<q<<"\n";
	for(const auto& q:removeQueries)std::cout<<"REMOVE:"<<q<<"\n";
	return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
