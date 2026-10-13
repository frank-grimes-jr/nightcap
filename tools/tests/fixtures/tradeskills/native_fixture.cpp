// Boundaries for actual GetTradeRecipe / HandleCombine bodies. Recipe SQL is
// executed by Python's real SQLite engine; no matching algorithm lives here.
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
using uint8=uint8_t; using uint16=uint16_t; using uint32=uint32_t;
using int16=int16_t; using int32=int32_t; using uint64=uint64_t;
namespace fmt {
template<class T> std::string value(const T& v) {std::ostringstream s;s<<v;return s.str();}
inline std::string value(uint8 v) {return std::to_string(v);}
inline std::string format(std::string s) {return s;}
template<class T,class... Rest> std::string format(std::string s,const T& v,const Rest&... rest) {
 auto start=s.find("{}");if(start==std::string::npos)throw std::runtime_error("fixture format mismatch");
 s.replace(start,2,value(v));return format(s,rest...);
}
}
namespace Strings {
inline uint32 ToUnsignedInt(const char* s) {return uint32(std::stoul(s));}
inline int ToInt(const char* s) {return std::stoi(s);}
}
#define LogError(...) ((void)0)
#define LogTradeskills(...) ((void)0)
#define LogTradeskillsDetail(...) ((void)0)
#define RuleB(category,name) false
#define safe_delete(pointer) do {delete pointer;pointer=nullptr;} while(0)
namespace Chat {enum {Red,LightBlue,Emote,Yellow,Skills,White};}
namespace Class {enum {Shaman=10,Rogue=9};}
namespace Race {enum {Gnome=12};}
enum {OP_TradeSkillCombine,OP_ClearObject,TRANSFORM_COMPLETE,TRANSFORM_FAILED,DETRANSFORM_FAILED,
 TRADESKILL_NOCOMBINE,TRADESKILL_LEARN_RECIPE,EVENT_COMBINE,EVENT_COMBINE_VALIDATE,
 EVENT_COMBINE_SUCCESS,EVENT_COMBINE_FAILURE,ItemPacketWorldContainer,OP_RecipeAutoCombine,
 TRADESKILL_MISSING_COMPONENTS,MIN_LEVEL_ALCHEMY=25};
namespace EQ {
namespace invslot {enum {SLOT_TRADESKILL_EXPERIMENT_COMBINE=1000,slotCursor=30,GENERAL_BEGIN=22,GENERAL_END=29};}
namespace invbag {enum {SLOT_BEGIN=0,SLOT_COUNT=10};}
namespace invtype {enum {WORLD_SIZE=10};}
namespace item {enum {ItemClassBag=1,BagTypeTransformationmold=253,BagTypeDetransformationmold=254};}
namespace skills {enum SkillType {SkillAlchemy=59,SkillTinkering=57,SkillMakePoison=56,SkillBaking=60};}
struct ItemData {uint32 ID=0;uint8 BagType=10;uint8 BagSlots=10;int Icon=0;bool Stackable=true;const char* Name="fixture";const char* IDFile="IT0";};
struct ItemInstance {
 ItemData data;int charges=1;bool bag=false,augmented=false,retired=false,has_item=true;
 std::map<int,std::unique_ptr<ItemInstance>> contents;
 ItemInstance(uint32 id,int quantity,bool stackable=true):charges(quantity) {data.ID=id;data.Stackable=stackable;}
 void valid() const {if(retired)throw std::runtime_error("retired container pointer accessed after quest callback");}
 const ItemData* GetItem() const {valid();return has_item?&data:nullptr;}
 uint32 GetID() const {valid();return has_item?data.ID:0;}
 ItemInstance* GetItem(int slot) const {valid();auto i=contents.find(slot);return i==contents.end()?nullptr:i->second.get();}
 bool IsType(int type) const {return bag&&type==item::ItemClassBag;}
 bool IsClassBag() const {valid();return bag;}
 bool IsStackable() const {return data.Stackable;}
 int GetCharges() const {return charges;}
 void SetCharges(int n) {charges=n;}
 bool IsAugmented() const {return augmented;}
 int GetAugmentItemID(int) const {return 0;}
 bool IsAttuned() const {return false;}
 int GetOrnamentationIcon() const {return 0;}
 static bool CanTransform(const ItemData*,const ItemData*,bool) {return false;}
 void Clear() {valid();contents.clear();}
 void DeleteItem(int slot) {contents.erase(slot);}
 ItemInstance* PopItem(int slot) {auto p=GetItem(slot);if(p)contents.at(slot).release();contents.erase(slot);return p;}
 void add(int slot,uint32 id,int quantity,bool stackable=true) {contents[slot]=std::make_unique<ItemInstance>(id,quantity,stackable);}
};
struct InventoryProfile {
 ItemInstance* bag=nullptr;bool cursor=false;
 std::map<int,std::unique_ptr<ItemInstance>> general;
 struct Lookup {uint64 PossessionsBitmask=~uint64{0};} lookup;
 static int CalcSlotId(int parent,int child) {return parent*100+child;}
 ItemInstance* GetItem(int slot) {
  if(slot==22)return bag;
  if(slot>=2200){auto parent=GetItem(slot/100);return parent?parent->GetItem(slot%100):nullptr;}
  const auto found=general.find(slot);return found==general.end()?nullptr:found->second.get();
 }
 void add(int slot,uint32 id,int quantity,bool stackable=true) {general[slot]=std::make_unique<ItemInstance>(id,quantity,stackable);}
 void erase(int slot) {if(slot==22)bag=nullptr;else if(slot>=2200){auto parent=GetItem(slot/100);if(parent)parent->DeleteItem(slot%100);}else general.erase(slot);}
 const Lookup* GetLookup() const {return &lookup;}
 bool CursorEmpty() const {return !cursor;}
};
}
struct DBTradeskillRecipe_Struct {
 EQ::skills::SkillType tradeskill=EQ::skills::SkillBaking;int16 skill_needed=0;uint16 trivial=1;
 bool nofail=true,replace_container=false;
 std::vector<std::pair<uint32,uint8>> onsuccess,onfail,salvage;
 std::string name="fixture";uint8 must_learn=0;bool has_learnt=true;uint32 madecount=0,recipe_id=0;bool quest=false;
};
struct NewCombine_Struct {int container_slot=22,guildtribute_slot=0;};
struct RecipeAutoCombine_Struct {uint32 object_type=10,some_id=999,unknown1=22,recipe_id=1,reply_code=0;};
struct ClearObject_Struct {int Clear=0;};
struct EQApplicationPacket {
 int opcode;unsigned char* pBuffer;
 EQApplicationPacket(int op,int size):opcode(op),pBuffer(new unsigned char[std::max(size,1)]{}) {}
 ~EQApplicationPacket() {delete[] pBuffer;}
};
struct PlayerProfile_Struct {int class_=1,level=50,race=1;};
struct Object;
using Snapshot=std::map<int,std::pair<uint32,int>>;
Snapshot snapshot(const EQ::ItemInstance* bag) {
 Snapshot result;for(const auto& [slot,inst]:bag->contents)result[slot]={inst->data.ID,inst->charges};return result;
}
struct Client {
 EQ::InventoryProfile inv;PlayerProfile_Struct profile;int attempts=0,acks=0;uint32 chosen=0;
 Object* world=nullptr;Snapshot displayed;
 bool connected=true,loaded=true,zoning=false,dead=false,engaged=false,stunned=false,mezzed=false,feared=false,ai=false;
 bool lore=false,execution_success=true,push_output=false;int skill=300;float x=0,y=0,z=0;
 struct Trade {bool active=false;void* With() const {return active?(void*)this:nullptr;}} trade_value;
 Trade* trade=&trade_value;
 std::vector<std::string> timeline,markers;std::vector<uint32> replies;
 EQ::InventoryProfile& GetInv() {return inv;}
 PlayerProfile_Struct& GetPP() {return profile;}
 template<class... T> void Message(int,const char* text,T... args) {
  if(std::string(text).starts_with("[NCTS1]")) {char buffer[256];std::snprintf(buffer,sizeof(buffer),text,args...);markers.emplace_back(buffer);timeline.push_back("marker");}
 }
 template<class... T> void MessageString(T...) {}
 template<class... T> void SummonItem(T...) {}
 void QueuePacket(EQApplicationPacket* p) {
  if(p->opcode==OP_TradeSkillCombine)++acks;
  else if(p->opcode==OP_ClearObject)displayed.clear();
  else if(p->opcode==OP_RecipeAutoCombine){replies.push_back(reinterpret_cast<RecipeAutoCombine_Struct*>(p->pBuffer)->reply_code);timeline.push_back("ack");}
 }
 Object* GetTradeskillObject() const {return world;}
 void SendItemPacket(int slot,const EQ::ItemInstance* item,int) {displayed[slot]={item->data.ID,item->charges};}
 int GetSkill(EQ::skills::SkillType) const {return skill;}
 bool CheckTradeskillLoreConflict(uint32) const {return lore;}
 uint32 CharacterID() const {return 1;}
 uint32 GetID() const {return 42;}
 int GetClass() const {return profile.class_;}int GetLevel() const {return profile.level;}int GetRace() const {return profile.race;}
 float GetX() const{return x;}float GetY() const{return y;}float GetZ() const{return z;}
 bool Connected() const{return connected;}bool ClientDataLoaded() const{return loaded;}bool IsZoning() const{return zoning;}
 bool IsDead() const{return dead;}bool IsEngaged() const{return engaged;}bool IsStunned() const{return stunned;}
 bool IsMezzed() const{return mezzed;}bool IsFeared() const{return feared;}bool IsAIControlled() const{return ai;}
 bool TradeskillExecute(DBTradeskillRecipe_Struct* spec) {++attempts;chosen=spec->recipe_id;timeline.push_back("execute");if(push_output)inv.cursor=true;return execution_success;}
 void DeleteItemInInventory(int slot,int quantity,bool) {
  const auto inst=inv.GetItem(slot);if(!inst)return;
  if(quantity>0&&inst->IsStackable()&&inst->charges>quantity)inst->charges-=quantity;
  else inv.erase(slot);
 }
};
struct QueryResult {
 std::vector<std::vector<std::string>> rows;
 struct Iterator {
  const QueryResult* r;size_t row;
  const char* operator[](size_t col) const {return r->rows.at(row).at(col).c_str();}
  Iterator operator*() const {return *this;}
  Iterator& operator++() {++row;return *this;}
  bool operator!=(const Iterator& other) const {return row!=other.row;}
 };
 Iterator begin() const {return {this,0};}
 Iterator end() const {return {this,rows.size()};}
 bool Success() const {return true;}
 size_t RowCount() const {return rows.size();}
 std::string ErrorMessage() const {return "";}
};
bool replace_container_fixture=false;
DBTradeskillRecipe_Struct recipe_fixture;
bool recipe_found_fixture=true;
struct ZoneDatabase {
 bool GetTradeRecipe(const EQ::ItemInstance*,uint8,uint32,Client*,DBTradeskillRecipe_Struct*,bool*);
 bool GetTradeRecipe(uint32 id,uint8,uint32,Client*,DBTradeskillRecipe_Struct* spec) {*spec=recipe_fixture;spec->recipe_id=id;spec->replace_container=replace_container_fixture;return recipe_found_fixture;}
 QueryResult QueryDatabase(const std::string& query) {
  std::cout<<"QUERY "<<query<<std::endl;std::string line;
  if(!std::getline(std::cin,line))throw std::runtime_error("query response missing");
  QueryResult result;const auto count=std::stoul(line);
  for(size_t i=0;i<count;++i){std::getline(std::cin,line);const auto columns=std::stoul(line);std::vector<std::string> row;
   for(size_t j=0;j<columns;++j){std::getline(std::cin,line);row.push_back(line);}result.rows.push_back(row);}
  return result;
 }
} content_db;
struct Database {
 std::map<uint32,EQ::ItemData> items;
 Snapshot saved;int saves=0;
 const EQ::ItemData* GetItem(uint32 id) {auto i=items.find(id);return i==items.end()?nullptr:&i->second;}
 void DeleteWorldContainer(uint32,uint32) {saved.clear();++saves;}
 void SaveWorldContainer(uint32,uint32,const EQ::ItemInstance* bag) {saved=snapshot(bag);++saves;}
 void UpdateRecipeMadecount(uint32,uint32,uint32) {}
} database;
struct Zone {uint32 GetZoneID() const {return 1;}} zone_instance;
auto* zone=&zone_instance;
struct Parser {
 int event=-1,result=0;std::function<void(Client*)> action;
 bool PlayerHasQuestSub(int id) {return event==id;}
 template<class... T>int EventPlayer(int id,Client* user,T...) {if(id==event){user->timeline.push_back("callback");if(action)action(user);}return result;}
} parser;
auto* parse=&parser;
namespace PlayerEvent {enum {COMBINE_SUCCESS,COMBINE_FAILURE};struct CombineEvent {uint32 recipe_id;std::string recipe_name;uint32 made_count;uint32 tradeskill_id;};}
struct PlayerEventLogs {static PlayerEventLogs* Instance(){static PlayerEventLogs p;return &p;}bool IsEventEnabled(int){return false;}};
template<class... T> void RecordPlayerEventLogWithClient(T...) {}
struct Object {uint8 m_type=10;uint32 m_id=1;EQ::ItemInstance* m_inst=nullptr;Client* user=nullptr;float x=0,y=0,z=0;
 float GetX() const{return x;}float GetY() const{return y;}float GetZ() const{return z;}
 void HandleCombine(Client*,const NewCombine_Struct*,Object*);
 void HandleAutoCombine(Client*,const RecipeAutoCombine_Struct*);};
void check(bool okay,const char* message) {if(!okay)throw std::runtime_error(message);}
int quantity(const EQ::ItemInstance& bag,uint32 id) {
 int total=0;for(const auto& [slot,inst]:bag.contents)if(inst->data.ID==id)total+=inst->IsStackable()?inst->charges:1;
 return total;
}
