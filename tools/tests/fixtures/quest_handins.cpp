#include <algorithm>
#include <cstdint>
#include <iostream>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
using uint32 = uint32_t;
using uint16 = uint16_t;
struct Item { uint32 ID; std::string Name; bool stackable = false; };
namespace EQ {
struct ItemInstance {
	Item *definition;
	int charges = 1;
	bool attuned = true;
	std::string custom = "preserved";
	static inline std::vector<std::unique_ptr<ItemInstance>> clones;
	const Item *GetItem() const { return definition; }
	uint32 GetID() const { return definition->ID; }
	bool IsStackable() const { return definition->stackable; }
	int GetCharges() const { return charges; }
	void SetCharges(int n) { charges = n; }
	std::vector<uint32> GetAugmentIDs() const { return {7}; }
	std::vector<std::string> GetAugmentNames() const { return {"preserved augment"}; }
	ItemInstance *Clone() const { clones.emplace_back(new ItemInstance(*this)); return clones.back().get(); }
};
}
struct Database {
	std::map<uint32, Item> items;
	const Item *GetItem(uint32 id) { auto i = items.find(id); return i == items.end() ? nullptr : &i->second; }
} database;
namespace Strings {
bool IsNumber(const std::string &s) { return !s.empty() && s.find_first_not_of("0123456789") == std::string::npos; }
uint32 ToUnsignedInt(const std::string &s) { return std::stoul(s); }
}
namespace fmt { template<class... T> std::string format(const char *, T...) { return ""; } }
#define LogNpcHandin(...) ((void)0)
#define LogNpcHandinDetail(...) ((void)0)
namespace PlayerEvent {
constexpr int NPC_HANDIN=1;
struct HandinEntry { uint32 item_id; std::string item_name; std::vector<uint32> augment_ids; std::vector<std::string> augment_names; uint16 charges; };
struct HandinMoney { uint32 platinum=0,gold=0,silver=0,copper=0; };
struct HandinEvent { uint32 npc_id; std::string npc_name; std::vector<HandinEntry> handin_items; HandinMoney handin_money;
	std::vector<HandinEntry> return_items; HandinMoney return_money; bool is_quest_handin; };
}
struct PlayerEventLogs { static PlayerEventLogs *Instance(){static PlayerEventLogs log; return &log;} bool IsEventEnabled(int){return false;} };
constexpr int EVENT_TRADE=1;
struct Parser { bool HasQuestSub(uint32,int){return true;} } parser;
Parser *parse=&parser;
#define RecordPlayerEventLogWithClient(...) ((void)0)
struct Client {
	std::vector<EQ::ItemInstance> returned;
	std::vector<uint32> external;
	PlayerEvent::HandinMoney money;
	int money_calls = 0;
	const char *GetCleanName() { return "Player"; }
	void TrainDiscipline(uint32) {}
	const std::vector<uint32> &GetExternalHandinItemsReturned() { return external; }
	PlayerEvent::HandinMoney GetExternalHandinMoneyReturned() { return {}; }
	void PushItemOnCursor(const EQ::ItemInstance &i,bool) { returned.push_back(i); }
	void AddMoneyToPP(uint32 c,uint32 s,uint32 g,uint32 p,bool) {
		money.platinum+=p; money.gold+=g; money.silver+=s; money.copper+=c; ++money_calls;
	}
};
struct NPC {
// HANDIN_STRUCTS
	Handin m_hand_in;
	bool m_handin_started = false, multi = false;
	bool m_has_processed_handin_return = false;
	bool IsMultiQuestEnabled() { return multi; }
	bool IsGuildmaster() { return false; }
	bool IsGuildmasterForClient(Client *) { return false; }
	bool IsDisciplineTome(const Item *) { return false; }
	void Say(const char *) {}
	const char *GetCleanName() { return "Quest NPC"; }
	uint32 GetNPCTypeID() { return 14075; }
	void ResetMultiQuest() { m_hand_in = {}; }
	bool CheckHandin(Client *, std::map<std::string, uint32>, std::map<std::string, uint32>, std::vector<EQ::ItemInstance *>);
	Handin ReturnHandinItems(Client *);
};
// CHECK_HANDIN_METHOD

void require(bool ok, const char *message) { if (!ok) throw std::runtime_error(message); }
int main() { try {
	Client c;
	for (auto [id, name] : std::map<uint32, std::string>{{13737,"Aviak Charm"},{213737,"Aviak Charm (Polished)"},
		{413737,"Aviak Charm (Exalted)"},{613737,"Aviak Charm (Ascended)"},{813737,"Aviak Charm (Ascended)"},
		{10032,"Star Ruby"},{13738,"Wrong Charm"},{213738,"Aviak Charm (Polished)"},{213739,"Wrong Charm (Polished)"},
		{940000,"Hunt Base"},{940001,"Hunt Polished"},{960000,"Dungeon Normal"},{960001,"Dungeon Polished"}})
		database.items.emplace(id, Item{id, name});
	database.items.at(10032).stackable = true;
	auto inst = [](uint32 id, int count = 1) { return EQ::ItemInstance{&database.items.at(id), count}; };
	for (auto [base, name] : std::map<uint32, std::string>{{3140,"Darkforge Helm"},{3141,"Darkforge Breastplate"},{3145,"Darkforge Greaves"}}) {
		for (auto [offset, suffix] : std::map<uint32, std::string>{{0,""},{200000," (Polished)"},{400000," (Exalted)"},{600000," (Ascended)"}})
			database.items.emplace(base+offset, Item{base+offset,name+suffix});
	}
	for (uint32 helm : {3140u,203140u,403140u,603140u}) {
		for (uint32 breast : {3141u,203141u,403141u,603141u}) {
			for (uint32 legs : {3145u,203145u,403145u,603145u}) {
				NPC n; auto h=inst(helm),b=inst(breast),l=inst(legs);
				// Kurron selects exact Ascended IDs when present, otherwise Normal requirements.
				auto req=[](uint32 id){return std::to_string(id>=600000?id:id%200000);};
				require(n.CheckHandin(&c, {{"platinum",900}}, {{req(helm),1},{req(breast),1},{req(legs),1},{"platinum",900}}, {&h,&b,&l}), "mixed Darkforge rejected");
				require(n.m_hand_in.items.empty(), "Darkforge ingredients not consumed");
				c.money={}; c.money_calls=0;
				c.AddMoneyToPP(0,0,0,900,true); // actual Kurron success callback calls givecash once
				n.ReturnHandinItems(&c);
				require(c.money.platinum==900 && c.money_calls==1, "duplicate Darkforge cash refund");
			}
		}
	}
	{
		NPC n; auto h=inst(203140), b=inst(403141), l=inst(603145), extra=inst(13738);
		std::map<std::string,uint32> coins={{"platinum",901},{"gold",1},{"silver",2},{"copper",3}};
		auto required=coins; required.insert({{"3140",1},{"3141",1},{"603145",1}});
		require(n.CheckHandin(&c,coins,required,{&h,&b,&l,&extra}), "mixed coins rejected");
		c.money={}; c.money_calls=0; c.returned.clear(); c.AddMoneyToPP(3,2,1,901,true);
		n.ReturnHandinItems(&c);
		require(c.money_calls==1 && c.money.platinum==901 && c.money.gold==1 && c.money.silver==2 && c.money.copper==3, "excess coins duplicated/lost");
		require(c.returned.size()==1 && c.returned[0].GetID()==13738, "Darkforge extra not returned");
		NPC missing;
		require(!missing.CheckHandin(&c,coins,required,{&h,&l}), "missing Darkforge piece accepted");
		c.money={}; c.money_calls=0; c.returned.clear(); missing.ReturnHandinItems(&c);
		require(c.money_calls==1 && c.money.platinum==901 && c.returned.size()==2, "failed Darkforge return lost items/coins");
	}
	for (uint32 id : {13737u, 213737u, 413737u, 613737u}) {
		NPC n; auto charm = inst(id), ruby = inst(10032, 3), extra = inst(13738);
		require(n.CheckHandin(&c, {}, {{"13737",1},{"10032",2}}, {&charm,&ruby,&extra}), "Aviak tier rejected");
		require(n.m_hand_in.items.size() == 2, "wrong leftovers");
		require(n.m_hand_in.items[0].item_id == "10032" && n.m_hand_in.items[0].count == 1, "stack remainder");
		require(n.m_hand_in.items[1].item->custom == "preserved" && n.m_hand_in.items[1].item->attuned, "instance lost");
		c.returned.clear(); n.ReturnHandinItems(&c);
		require(c.returned.size()==2 && c.returned[0].GetID()==10032 && c.returned[0].GetCharges()==1, "incorrect native stack return");
		require(c.returned[1].custom=="preserved" && c.returned[1].attuned, "native return lost instance state");
	}
	for (uint32 id : {13738u,213738u,213739u,813737u,940001u,960001u}) {
		NPC n; auto wrong = inst(id), ruby = inst(10032, 2);
		require(!n.CheckHandin(&c, {}, {{"13737",1},{"10032",2}}, {&wrong,&ruby}), "unrelated family accepted");
		require(n.m_hand_in.items.size() == 2 && n.m_hand_in.items[1].count == 2, "failed check consumed items");
	}
	{
		NPC n; auto charm = inst(613737), ruby = inst(10032, 1);
		require(!n.CheckHandin(&c, {}, {{"13737",1},{"10032",2}}, {&charm,&ruby}), "missing ruby accepted");
		require(n.m_hand_in.items[0].item->GetID() == 613737 && n.m_hand_in.items[0].count == 1, "tier changed on failure");
	}
	{
		NPC n; auto charm = inst(213737);
		require(!n.CheckHandin(&c, {}, {{"13737",1},{"platinum",1}}, {&charm}), "missing money accepted");
		require(n.m_hand_in.items[0].count == 1, "failed money check consumed tiered item");
		require(n.CheckHandin(&c, {}, {{"13737",1}}, {&charm}), "later branch lost tiered item");
		require(!n.CheckHandin(&c, {}, {{"13737",1}}, {&charm}), "reused consumed item");
	}
	for (bool multi : {false,true}) {
		NPC n; n.multi = multi; auto charm = inst(213737);
		require(!n.CheckHandin(&c, {}, {{"13737",1},{"213737",1}}, {&charm}), "one instance satisfied two requirements");
		NPC both; both.multi = multi; auto normal = inst(13737);
		require(both.CheckHandin(&c, {}, {{"13737",1},{"213737",1}}, {&charm,&normal}), "explicit quality not reserved");
	}
	{
		NPC n; auto p = inst(213737), normal = inst(13737);
		require(n.CheckHandin(&c, {}, {{"13737",1}}, {&p,&normal}), "normal requirement");
		require(n.m_hand_in.items.size() == 1 && n.m_hand_in.items[0].item_id == "213737", "consumed higher tier before exact");
	}
	for (uint32 id : {13737u,413737u,613737u}) {
		NPC n; auto item = inst(id);
		require(!n.CheckHandin(&c, {}, {{"213737",1}}, {&item}), "explicit tier weakened");
	}
	{
		NPC n; auto charm = inst(213737);
		require(!n.CheckHandin(&c, {}, {{"199999",1}}, {&charm}), "unknown required ID accepted");
		NPC empty; require(!empty.CheckHandin(&c, {}, {{"199999",1}}, {}), "unknown requirement became free reward");
		NPC mixed; require(!mixed.CheckHandin(&c, {}, {{"13737",1},{"199999",1}}, {&charm}), "unknown requirement ignored");
		c.returned.clear(); mixed.ReturnHandinItems(&c);
		require(c.returned.size()==1 && c.returned[0].GetID()==213737 && c.returned[0].custom=="preserved", "failed return downgraded item");
	}
	{
		NPC n; auto p=inst(213737), e=inst(413737);
		require(n.CheckHandin(&c, {}, {{"13737",2}}, {&p,&e}), "mixed native quantities failed");
		NPC name; database.items.at(213737).Name="Unrelated (Polished)";
		require(!name.CheckHandin(&c, {}, {{"13737",1}}, {&p}), "numeric collision bypassed name check");
		database.items.at(213737).Name="Aviak Charm (Polished)";
	}
	{
		NPC n; n.multi = true; auto charm = inst(413737), ruby = inst(10032,2);
		require(!n.CheckHandin(&c, {}, {{"13737",1},{"10032",2}}, {&charm}), "partial multiquest accepted");
		require(n.m_hand_in.items[0].is_multiquest_item, "tier not retained for multiquest");
		c.returned.clear(); n.ReturnHandinItems(&c);
		require(c.returned.empty(), "multiquest returned retained tier");
		n.m_handin_started = false; // next player trade, after native ResetHandin
		require(n.CheckHandin(&c, {}, {{"13737",1},{"10032",2}}, {&ruby}), "multiquest tier rejected");
	}
	std::cout << "Native hand-in regressions passed\n";
} catch (const std::exception &e) { std::cerr << e.what() << '\n'; return 1; } }
