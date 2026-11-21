// Diagnostic only: timed primary-hand NPC pressure, not a full encounter/AI simulation.
#include "zone/client.h"
#include "zone/zone.h"
#include "zone/entity.h"
#include "zone/npc.h"
#include "zone/aa_ability.h"
#include "zone/nightcap_heroic_cast.h"
#include "common/json/json.hpp"
#include "common/item_instance.h"
#include "common/raid_augment.h"
#include "common/ptimer.h"
#include "common/deity.h"
#include <filesystem>
#include <fstream>
#include <set>
#include <sys/time.h>
using json=nlohmann::json;
extern Zone *zone;
extern volatile bool is_zone_loaded;
extern uint32 current_time,last_time;
extern double frame_time;
static uint32 seed=20261120;
static bool virtual_clock=false;
static uint64_t elapsed=0;
extern "C" unsigned int __wrap__ZNSt13random_device9_M_getvalEv(void*){return seed;}
extern "C" int __real_gettimeofday(timeval*,void*);
extern "C" time_t __real_time(time_t*);
extern "C" int __wrap_gettimeofday(timeval *v,void *tz){
	if(!virtual_clock)return __real_gettimeofday(v,tz);
	if(tz)throw std::runtime_error("diagnostic timezone");
	v->tv_sec=1789171200+elapsed/1000;v->tv_usec=(elapsed%1000)*1000;return 0;
}
extern "C" time_t __wrap_time(time_t *p){if(!virtual_clock)return __real_time(p);time_t n=1789171200+elapsed/1000;if(p)*p=n;return n;}
static void check(bool ok,const std::string &why){if(!ok)throw std::runtime_error(why);}
static void advance(uint32 ms){elapsed+=ms;frame_time=ms/1000.0;Timer::SetCurrentTime();check(Timer::GetCurrentTime()==elapsed,"clock drift");}
bool NightcapBalancePreflight(int argc,char **argv){
	if(argc!=4||std::string(argv[1])!="tests:balance"||std::filesystem::current_path()!="/tmp/nightcap-classic-equipment-paths-20261121")return false;
	std::ifstream f("eqemu_config.json");json c;f>>c;auto&s=c["server"];
	return s["database"]["db"]=="nightcap_balance_20260912"&&s["database"]["username"]=="nightcap_balance"&&s["auto_database_updates"]=="false"&&!s.contains("content_database");
}
class Subject:public Client{
	std::vector<std::unique_ptr<EQ::ItemData>> owned;
	std::set<int> lore;
public:
	using Mob::GetFocusEffect;
    using Client::CalcHPRegen;
    using Client::CalcManaRegen;
    json offense_stats(){SetAttackTimer();auto v=GetItemBonuses();return {{"haste",static_cast<const Client*>(this)->GetHaste()},{"item_haste",v.haste},{"atk",GetATK()},{"item_atk",v.ATK},{"accuracy",v.Accuracy[EQ::skills::HIGHEST_SKILL+1]},{"interval_ms",GetAttackTimer().GetSetAtTrigger()}};}
    json defensive_stats(){auto v=GetItemBonuses();return {{"dodge",v.DodgeChance},{"parry",v.ParryChance},{"block",v.IncreaseBlockChance},{"hp_regen_item",v.HPRegen},{"mana_regen_item",v.ManaRegen},{"hp_regen_combat",CalcHPRegen(true)},{"mana_regen_combat",CalcManaRegen(true)},{"hp_regen_cap",CalcHPRegenCap()},{"mana_regen_cap",CalcManaRegenCap()}};}
    json rolls(Subject *attacker,bool behind,bool ranged){
        SetPosition(0,0,0);SetHeading(0);attacker->SetPosition(0,5,0);
        if(attacker->BehindMob(this,attacker->GetX(),attacker->GetY())!=behind)attacker->SetPosition(0,-5,0);
        check(attacker->BehindMob(this,attacker->GetX(),attacker->GetY())==behind,"facing control");
        int dodge=0,parry=0,block=0,riposte=0;
        for(int n=0;n<20000;n++){DamageHitInfo hit{};hit.hand=ranged?EQ::invslot::slotRange:EQ::invslot::slotPrimary;hit.skill=ranged?EQ::skills::SkillArchery:EQ::skills::Skill1HBlunt;AvoidDamage(attacker,hit);dodge+=hit.damage_done==DMG_DODGED;parry+=hit.damage_done==DMG_PARRIED;block+=hit.damage_done==DMG_BLOCKED;riposte+=hit.damage_done==DMG_RIPOSTED;}
        return {{"rolls",20000},{"dodge",dodge},{"parry",parry},{"block",block},{"riposte",riposte}};
    }
	bool dead=false;
	uint16 measured_heal_spell=0;
	bool completing_measured_cast=false;
	uint64 healed=0,overheal=0,damage=0,heal_events=0,main_heal_events=0,damaging_hits=0;
	bool Death(Mob*,int64,uint16,EQ::skills::SkillType,KilledByTypes,bool)override{dead=true;return true;}
	void HealDamage(uint64 amount,Mob *caster=nullptr,uint16 spell=SPELL_UNKNOWN)override{
		auto before=GetHP();Client::HealDamage(amount,caster,spell);auto gain=std::max<int64>(0,GetHP()-before);
		healed+=gain;overheal+=amount-gain;++heal_events;if(completing_measured_cast&&caster==this)++main_heal_events;
	}
	void Damage(Mob *from,int64 amount,uint16 spell,EQ::skills::SkillType skill,bool avoidable=true,int8 slot=-1,bool tick=false,eSpecialAttacks special=eSpecialAttacks::None)override{
		if(dead)return;auto before=GetHP();Client::Damage(from,amount,spell,skill,avoidable,slot,tick,special);
		auto loss=std::max<int64>(0,before-GetHP());damage+=loss;damaging_hits+=loss>0;
	}
	void pulse(){if(IsStunned()&&stunned_timer.Check())Mob::UnStun();completing_measured_cast=casting_spell_id==measured_heal_spell;Mob::SpellProcess();completing_measured_cast=false;}
	bool ready(){return !casting_spell_id&&!delaytimer&&!spellend_timer.Enabled()&&!IsStunned();}
	void init(const json &c){
		check(ClientFinishedLoading(),"diagnostic login completion adapter absent");
		class_=c["classes"][0];level=c["level"];race=base_race=c.value("race",1);deity=c.value("deity",396);auto&p=GetPP();p.class_=class_;p.level=level;p.race=race;p.deity=deity;
		p.STR=p.STA=p.AGI=p.DEX=p.INT=p.WIS=p.CHA=c.value("base_stat",100);p.hunger_level=p.thirst_level=6000;
		SetCharacterId(c.value("character_id",0));GetPTimers().SetCharID(CharacterID());LoadMulticlassMask();
		check(json(GetMulticlassList())==c["classes"],"synthetic multiclass row mismatch");
		SetClientVersion(EQ::versions::ClientVersion::RoF2);GetInv().SetInventoryVersion(EQ::versions::ClientVersion::RoF2);
		p.expansions=RuleB(World,UseClientBasedExpansionSettings)?EQ::expansions::ConvertClientVersionToExpansionsMask(ClientVersion()):RuleI(World,ExpansionSettings);
		std::fill(std::begin(p.InnateSkills),std::end(p.InnateSkills),InnateDisabled);
		for(int k=0;k<=EQ::skills::HIGHEST_SKILL;k++){
			uint16 cap=0;for(auto cl:GetMulticlassList())cap=std::max(cap,MaxSkill(static_cast<EQ::skills::SkillType>(k),cl,level));
			if(k>=EQ::skills::SkillSpecializeAbjure&&k<=EQ::skills::SkillSpecializeEvocation&&k!=EQ::skills::SkillSpecializeAlteration)cap=std::min<uint16>(cap,50);
			p.skills[k]=cap;
		}
		p.skills[EQ::skills::SkillChanneling]=std::min<int>(p.skills[EQ::skills::SkillChanneling],c.value("channeling",200));
		SetName("FocusProbe");SetPosition(0,0,0);SetHeading(0);SaveSpellLoc();
	}
	void legal(const EQ::ItemData *i,int slot){
		check(i&&CanEquipItem(i)&&i->ReqLevel<=GetLevel()&&(!i->Deity||(i->Deity&Deity::GetBitmask(GetDeity()))),"illegal item class/race/level/deity");
		check((i->Slots&(1u<<slot))!=0,"illegal equipment slot");
		int key=i->LoreGroup==-1?-int(i->ID):i->LoreGroup;if(key)check(lore.insert(key).second,"duplicate lore");
	}
	void equip(const json &r,const json &policy,bool after,bool exact){
		int slot=r[0];check(slot>=0&&slot<=21&&!GetInv().GetItem(slot),"duplicate/invalid slot");
		auto *i=database.GetItem(r[1]);legal(i,slot);auto copy=std::make_unique<EQ::ItemData>(*i);
		std::string key=std::to_string(i->ID);if(after&&policy.contains(key)){
            const auto &change=policy[key];
            if(change.contains("focus")){check(i->Focus.Effect<=0,"policy would replace focus");copy->Focus.Effect=change["focus"];copy->Focus.Type=6;}
            if(change.contains("worn")){check(i->Worn.Effect<=0,"policy would replace worn");copy->Worn.Effect=change["worn"];copy->Worn.Type=2;}
        }
		EQ::ItemInstance instance(copy.get(),1);owned.push_back(std::move(copy));
		int socket=0;for(int id:r[2]){if(id){auto*a=database.GetItem(id);legal(a,slot);int selected=exact?socket:instance.AvailableAugmentSlot(a->AugType);check(selected>=0&&instance.IsAugmentSlotAvailable(a->AugType,selected)&&!IsAugmentRestricted(i->ItemType,a->AugRestrict)&&!instance.ContainsAugmentByID(id),"illegal augment socket/restriction/duplicate");if(NightcapRaidAug::IsReward(id))check(NightcapRaidAug::CanInsert(instance,selected,false),"raid augment socket");instance.PutAugment(selected,EQ::ItemInstance(a,1));}++socket;}
		check(GetInv().PutItem(slot,instance)==slot,"inventory insert");
	}
	json purchase(const json &c){
		GetPP().aapoints=c.value("aa_budget",0);json rows=json::array();
		for(auto &id:c.value("aa_rank_ids",json::array())){
			auto*r=zone->GetAlternateAdvancementRank(id.get<uint32>());
			check(r&&r->cost>=0&&CanPurchaseAlternateAdvancementRank(r,true,true),"AA purchase gate rejected "+id.dump()+" case "+c["id"].get<std::string>());
			check(SetAA(r->id,r->current_value,r->base_ability->charges),"SetAA rejected");
			GetPP().aapoints-=r->cost;GetPP().aapoints_spent+=r->cost;
			rows.push_back({{"rank",r->id},{"cost",r->cost},{"name",r->base_ability->name}});
		}
		return rows;
	}
	// Synthetic focus placement on real legal hosts/augments, in memory only.
	void control_item(int slot,int host,int focus,int worn,int augfocus){
		auto *stock=database.GetItem(host);legal(stock,slot);auto h=std::make_unique<EQ::ItemData>(*stock);
		h->Focus.Effect=focus;h->Focus.Type=6;h->Worn.Effect=worn;h->Worn.Type=2;
		EQ::ItemInstance inst(h.get(),1);owned.push_back(std::move(h));
		if(augfocus){auto *stockaug=database.GetItem(609607);legal(stockaug,slot);auto a=std::make_unique<EQ::ItemData>(*stockaug);
			a->Focus.Effect=augfocus;a->Focus.Type=6;a->Worn.Effect=0;int socket=inst.AvailableAugmentSlot(a->AugType);
			check(socket>=0&&!IsAugmentRestricted(stock->ItemType,a->AugRestrict),"control augment legal socket");inst.PutAugment(socket,EQ::ItemInstance(a.get(),1));owned.push_back(std::move(a));}
		check(GetInv().PutItem(slot,inst)==slot,"control item insert");
	}
};
class Threat:public NPC{
public:
	using NPC::NPC;bool dead=false;
	bool Death(Mob*,int64,uint16,EQ::skills::SkillType,KilledByTypes,bool)override{dead=true;return true;}
};
int NightcapBalanceMain(int argc,char **argv){
	EQEmuLogSys::Instance()->SilenceConsoleLogging();std::ifstream f(argv[2]);json input;f>>input;
	for(auto&r:input["rules"])check(RuleManager::Instance()->SetRule(r[0],r[1]),"rule");
	virtual_clock=true;current_time=last_time=0;Timer::SetCurrentTime();
	zone=new Zone(32,0,"soldungb");check(zone->LoadZoneCFG("soldungb",0)&&zone->CanDoCombat(),"native arena config missing/combat disabled");zone->LoadBaseData();zone->LoadAlternateAdvancement();is_zone_loaded=true;
	if(!input["cases"].empty()||input.contains("offense_cases")){zone->ReloadMaps();check(zone->zonemap&&zone->pathing&&zone->watermap,"native arena maps missing");}
	json out={{"scope","Controlled timed native primary-hand attacks and native self-heal casting. Six-second native combat regeneration; no NPC AI, outgoing attack policy, buff ticking, pathing, or player acceptance. AA gate plus in-memory usable ranks, not persisted earned ownership."},{"cases",json::array()}};
	if(input.contains("defense_cases")){
        for(auto &c:input["defense_cases"])for(bool after:{false,true}){
            auto *p=new Subject();p->init(c);for(auto&r:c["slots"])p->equip(r,input["policy"],after,c.value("exact_sockets",true));auto aa=p->purchase(c);p->CalcBonuses();
            auto *attacker=new Subject();attacker->init(c);attacker->CalcBonuses();
            json row={{"id",c["id"]},{"stage",after?"after":"before"},{"stats",p->defensive_stats()},{"offense",p->offense_stats()},{"aa",aa}};
            for(bool back:{false,true})for(bool ranged:{false,true}){seed=20261121;zone->random.Reseed();EQ::Random::Instance()->Reseed();row["rolls"].push_back({{"back",back},{"ranged",ranged},{"counts",p->rolls(attacker,back,ranged)}});}
            out["defense_cases"].push_back(row);
        }
    }
    for(auto &c:input.value("offense_cases",json::array()))for(bool after:{false,true}){
        seed=c.value("seed",42);zone->random.Reseed();EQ::Random::Instance()->Reseed();
        auto*p=new Subject();p->init(c);for(auto&r:c["slots"])p->equip(r,input["policy"],after,c.value("exact_sockets",true));auto aa=p->purchase(c);p->CalcBonuses();entity_list.AddClient(p);
        auto*type=content_db.LoadNPCTypesData(c.value("npc_id",32002));check(type,"offense NPC missing");
        auto*t=new Threat(type,nullptr,glm::vec4(0,5,0,256),GravityBehavior::Water);entity_list.AddNPC(t,false);p->SetTarget(t);
        json row={{"id",c["id"]},{"stage",after?"after":"before"},{"offense",p->offense_stats()},{"defense",p->defensive_stats()},{"aa",aa}};
        for(auto id:c.value("spells",json::array())){
            int spell=id;check(IsValidSpell(spell)&&p->GetSpellMinLevel(spell)<=p->GetLevel(),"offense spell not legal "+c["id"].get<std::string>()+" spell "+std::to_string(spell)+" minlevel "+std::to_string(p->GetSpellMinLevel(spell)));
            int effect=-1;for(int n=0;n<EFFECT_COUNT;n++)if(spells[spell].effect_id[n]==SpellEffect::CurrentHP&&spells[spell].base_value[n]<0){effect=n;break;}
            check(effect>=0,"damage effect missing");int base=p->CalcSpellEffectValue(spell,effect,p->GetLevel(),10,t);
            seed=c.value("seed",42);zone->random.Reseed();EQ::Random::Instance()->Reseed();
            auto amount=NightcapHeroicCast::Cast::Deliver(true,[&]{return spells[spell].buff_duration?p->GetActDoTDamage(spell,base,t):p->GetActSpellDamage(spell,base,t);});
            row["spells"].push_back({{"spell",spell},{"base",base},{"amount",amount},{"focus",p->GetFocusEffect(focusImprovedDamage,spell)}});
        }
        if(c.value("timed_melee",false)){
            p->SetHP(p->GetMaxHP());t->SetHP(t->GetMaxHP());p->SetAttackTimer();uint32 interval=p->GetAttackTimer().GetSetAtTrigger();check(interval>0,"melee timer missing");
            uint64 total=0;uint32 swings=0,hits=0,duration=120000;
            seed=c.value("seed",42);zone->random.Reseed();EQ::Random::Instance()->Reseed();
            for(uint32 ms=interval;ms<=duration;ms+=interval){advance(interval);auto hp=t->GetHP();p->Attack(t,EQ::invslot::slotPrimary);auto loss=std::max<int64>(0,hp-t->GetHP());total+=loss;hits+=loss>0;++swings;t->dead=false;t->SetHP(t->GetMaxHP());p->dead=false;p->SetHP(p->GetMaxHP());}
            row["melee"]={{"duration_ms",duration},{"swings",swings},{"damaging_swings",hits},{"damage",total},{"interval_ms",interval}};
        }
        out["offense_cases"].push_back(row);t->SetTarget(nullptr);t->WipeHateList();t->SetPosition(200000+out["offense_cases"].size()*1000,200000,0);p->SetTarget(nullptr);p->SetPosition(200000+out["offense_cases"].size()*1000,200000,0);
    }
    if(input.contains("category_matrix")){
		const auto *original_spells=spells;
		std::vector<SPDat_Spell_Struct> private_spells(spells,spells+SPDAT_RECORDS);
		spells=private_spells.data();
		auto reset_seed=[&]{seed=42;zone->random.Reseed();EQ::Random::Instance()->Reseed();};
		auto focus_spell=[&](int id,const std::vector<std::pair<int,int>>&effects){
			private_spells[id]=original_spells[id];
			for(int i=0;i<EFFECT_COUNT;i++){private_spells[id].effect_id[i]=SpellEffect::Blank;private_spells[id].base_value[i]=0;private_spells[id].limit_value[i]=0;}
			int i=0;for(auto e:effects){private_spells[id].effect_id[i]=e.first;private_spells[id].base_value[i]=e.second;private_spells[id].limit_value[i]=e.second;++i;}
		};
		for(bool classic:{false,true})for(int worn_mode:{0,1,2})for(bool strong_mana:{false,true}){
			check(RuleManager::Instance()->SetRule("Spells:UseClassicSpellFocus",classic?"true":"false"),"classic rule");
			check(RuleManager::Instance()->SetRule("Spells:UseAdditiveFocusFromWornSlotWithLimits",worn_mode==1?"true":"false"),"worn limits rule");
			check(RuleManager::Instance()->SetRule("Spells:UseAdditiveFocusFromWornSlot",worn_mode==2?"true":"false"),"worn rule");
			int h=strong_mana?10:20,m=strong_mana?30:10;
			for(std::string placement:{"none","healing_item","mana_item","both_items","heal_item_mana_aug","mana_item_heal_aug","both_aug","heal_worn_mana_item","mana_worn_heal_item","both_worn","multi_heal_first","multi_mana_first"}){
				focus_spell(2345,{{SpellEffect::ImprovedHeal,h}});focus_spell(2342,{{SpellEffect::ReduceManaCost,m}});
				if(placement=="multi_heal_first")focus_spell(2345,{{SpellEffect::ImprovedHeal,h},{SpellEffect::ReduceManaCost,m}});
				if(placement=="multi_mana_first")focus_spell(2345,{{SpellEffect::ReduceManaCost,m},{SpellEffect::ImprovedHeal,h}});
				auto *p=new Subject();p->init(input["category_matrix"]);
				if(placement=="healing_item")p->control_item(2,602191,2345,0,0);
				if(placement=="mana_item")p->control_item(2,602191,2342,0,0);
				if(placement=="both_items"){p->control_item(2,602191,2345,0,0);p->control_item(9,604344,2342,0,0);}
				if(placement=="heal_item_mana_aug")p->control_item(2,602191,2345,0,2342);
				if(placement=="mana_item_heal_aug")p->control_item(2,602191,2342,0,2345);
				if(placement=="both_aug"){p->control_item(2,602191,0,0,2345);p->control_item(9,604344,0,0,2342);}
				if(placement=="heal_worn_mana_item")p->control_item(2,602191,2342,2345,0);
				if(placement=="mana_worn_heal_item")p->control_item(2,602191,2345,2342,0);
				if(placement=="both_worn"){p->control_item(2,602191,0,2345,0);p->control_item(9,604344,0,2342,0);}
				if(placement.rfind("multi_",0)==0)p->control_item(2,602191,2345,0,0);
				p->CalcBonuses();int spell=17;json row={{"classic",classic},{"worn_mode",worn_mode},{"heal_endpoint",h},{"mana_endpoint",m},{"placement",placement}};
				reset_seed();row["direct_heal"]=p->CalcFocusEffect(focusImprovedHeal,2345,spell,true);
				reset_seed();row["direct_mana"]=p->CalcFocusEffect(focusManaCost,2345,spell,true);
				reset_seed();row["selected_heal"]=p->GetFocusEffect(focusImprovedHeal,spell);
				reset_seed();row["selected_mana"]=p->GetFocusEffect(focusManaCost,spell);
				reset_seed();row["mana_cost"]=p->GetActSpellCost(spell,spells[spell].mana);
				reset_seed();int base=p->CalcSpellEffectValue(spell,0,p->GetLevel(),10,p);row["healing"]=NightcapHeroicCast::Cast::Deliver(true,[&]{return p->GetActSpellHealing(spell,base,p);});
				out["category_matrix"].push_back(row);
			}
		}
		spells=original_spells;
		for(auto&r:input["rules"])check(RuleManager::Instance()->SetRule(r[0],r[1]),"restore rule");
	}
	for(auto &c:input.value("focus_controls",json::array())){
		auto*p=new Subject();p->init(c);for(auto&r:c["slots"])p->equip(r,c["policy"],true,true);p->CalcBonuses();
		int spell=c["heal_spell"],heal=c["heal_focus"],mana=c["mana_focus"];
		out["focus_controls"].push_back({{"id",c["id"]},{"base_mana",spells[spell].mana},
			{"direct_heal_as_heal",p->CalcFocusEffect(focusImprovedHeal,heal,spell)},
			{"direct_heal_as_mana",p->CalcFocusEffect(focusManaCost,heal,spell)},
			{"direct_mana_as_mana",p->CalcFocusEffect(focusManaCost,mana,spell)},
			{"direct_mana_as_heal",p->CalcFocusEffect(focusImprovedHeal,mana,spell)},
			{"selected_heal",p->GetFocusEffect(focusImprovedHeal,spell)},
			{"selected_mana",p->GetFocusEffect(focusManaCost,spell)},
			{"mana_cost",p->GetActSpellCost(spell,spells[spell].mana)}});
	}
	for(auto &c:input["cases"])for(bool after:{false,true}){
		seed=c.value("seed",20261120);zone->random.Reseed();EQ::Random::Instance()->Reseed();
		auto *player=new Subject();player->init(c);for(auto&r:c["slots"])player->equip(r,input["policy"],after,c.value("exact_sockets",true));
		auto aa=player->purchase(c);player->CalcBonuses();entity_list.AddClient(player);
		player->SetTarget(player);player->SetHP(player->GetMaxHP());player->SetMana(player->GetMaxMana());
		int spell=c["heal_spell"];check(IsValidSpell(spell)&&player->GetSpellMinLevel(spell)<=player->GetLevel(),"illegal healing spell "+std::to_string(spell)+" minlevel "+std::to_string(player->GetSpellMinLevel(spell))+" case "+c["id"].get<std::string>());player->GetPP().mem_spells[0]=spell;player->measured_heal_spell=spell;
		int base=player->CalcSpellEffectValue(spell,0,player->GetLevel(),10,player);
		json metrics={{"cast_ms",player->GetActSpellCasttime(spell,spells[spell].cast_time)},{"mana_cost_sample",player->GetActSpellCost(spell,spells[spell].mana)},{"healing_sample",NightcapHeroicCast::Cast::Deliver(true,[&]{return player->GetActSpellHealing(spell,base,player);})},
			{"hp",player->GetMaxHP()},{"mana",player->GetMaxMana()},{"heal_amount",player->GetHealAmt()},{"spell_damage",player->GetSpellDmg()},{"channeling",player->GetPP().skills[EQ::skills::SkillChanneling]},{"defensive",player->defensive_stats()}};
		const auto *type=content_db.LoadNPCTypesData(c["npc_id"]);check(type,"missing NPC");
		std::vector<Threat*> threats;std::vector<uint32> next,interval;
		for(int n=0;n<c.value("attackers",1);n++){
			auto*t=new Threat(type,nullptr,glm::vec4(0,5,0,256),GravityBehavior::Water);entity_list.AddNPC(t,false);t->SetTarget(player);t->SetAttackTimer();
			check(t->IsAttackAllowed(player),"native NPC attack not allowed");
			check(player->CombatRange(t),"outside melee range");auto timer=t->GetAttackTimer();auto delay=timer.GetDuration();check(delay>0,"NPC delay zero");threats.push_back(t);interval.push_back(delay);next.push_back(delay);
		}
		zone->random.Reseed();EQ::Random::Instance()->Reseed();
		uint32 start=Timer::GetCurrentTime(),duration=c.value("duration_ms",180000),retry=0,attempts=0,starts=0,swings=0,stunned_ms=0,landed_casts=0,failed_casts=0;
		uint64 regen_hp=0,regen_mana=0;
		uint64 receipt=0;bool pending=false;json trace=json::array();std::string result="duration";
		uint32 ms=0;
		for(;ms<=duration;ms+=10){
			for(size_t n=0;n<threats.size();n++)if(ms>=next[n]&&!threats[n]->dead&&!player->dead){threats[n]->Attack(player,EQ::invslot::slotPrimary);next[n]+=interval[n];++swings;}
			if(player->dead){result="player_death";break;}
			player->pulse();
            if(ms>0&&ms%6000==0){auto hp=player->GetHP(),mana=player->GetMana();player->SetHP(std::min(player->GetMaxHP(),hp+player->CalcHPRegen(true)));player->SetMana(std::min(player->GetMaxMana(),mana+player->CalcManaRegen(true)));regen_hp+=player->GetHP()-hp;regen_mana+=player->GetMana()-mana;}
			if(pending&&!player->IsCasting()){if(player->main_heal_events>receipt)++landed_casts;else ++failed_casts;pending=false;}
			if(player->IsStunned())stunned_ms+=10;
			if(ms>=retry&&player->ready()&&player->GetHPRatio()<=c.value("heal_at_percent",70)){
				++attempts;receipt=player->main_heal_events;bool accepted=player->CastSpell(spell,player->GetID(),EQ::spells::CastingSlot::Gem1);starts+=accepted;
				pending=accepted&&player->IsCasting();if(accepted&&!pending){if(player->main_heal_events>receipt)++landed_casts;else ++failed_casts;}retry=ms+250;
			}
			if(ms%1000==0)trace.push_back({ms,player->GetHP(),player->GetMana(),player->IsCasting(),player->IsStunned()});
			bool all_dead=std::all_of(threats.begin(),threats.end(),[](Threat*t){return t->dead;});if(all_dead){result="attackers_dead";break;}
			if(ms<duration)advance(10);
		}
		json row={{"id",c["id"]},{"stage",after?"after":"before"},{"seed",seed},{"metrics",metrics},{"aa",aa},{"spent_points",player->GetPP().aapoints_spent},{"result",result},{"elapsed_ms",std::min(ms,duration)},{"hp_end",player->GetHP()},{"mana_end",player->GetMana()},{"attempts",attempts},{"starts",starts},{"landed_casts",landed_casts},{"failed_started_casts",failed_casts},{"pending_cast",pending},{"swings",swings},{"damaging_hits",player->damaging_hits},{"damage",player->damage},{"healing",player->healed},{"hp_regen",regen_hp},{"mana_regen",regen_mana},{"overheal",player->overheal},{"stunned_ms",stunned_ms},{"npc_interval_ms",interval},{"trace",trace}};
		for(auto*t:threats)row["attackers"].push_back({{"hp_end",t->GetHP()},{"max_hp",t->GetMaxHP()},{"terminal",t->dead}});
		check(player->damage>0&&swings>0,"no actual NPC damage: "+c["id"].get<std::string>());
		check(attempts>0,"no healing attempts: "+c["id"].get<std::string>());
		out["cases"].push_back(row);
		{std::ofstream partial(std::string(argv[3])+".partial");partial<<out.dump(1);}
		// Objects deliberately retained until process exit: no logout, corpse, save, or cleanup callbacks.
		for(auto*t:threats){t->SetTarget(nullptr);t->WipeHateList();t->SetPosition(100000+out["cases"].size()*1000,100000,0);}player->SetTarget(nullptr);
		player->SetPosition(100000+out["cases"].size()*1000,100000,0);
	}
	std::ofstream result(argv[3]);result<<out.dump(1);return 0;
}
