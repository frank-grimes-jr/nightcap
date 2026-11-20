// Diagnostic only: timed primary-hand NPC pressure, not a full encounter/AI simulation.
#include "zone/client.h"
#include "zone/zone.h"
#include "zone/entity.h"
#include "zone/npc.h"
#include "zone/aa_ability.h"
#include "zone/nightcap_heroic_cast.h"
#include "common/json/json.hpp"
#include "common/item_instance.h"
#include "common/ptimer.h"
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
	if(argc!=4||std::string(argv[1])!="tests:balance"||std::filesystem::current_path()!="/tmp/nightcap-classic-focus-coverage-20261120")return false;
	std::ifstream f("eqemu_config.json");json c;f>>c;auto&s=c["server"];
	return s["database"]["db"]=="nightcap_balance_20260912"&&s["database"]["username"]=="nightcap_balance"&&s["auto_database_updates"]=="false"&&!s.contains("content_database");
}
class Subject:public Client{
	std::vector<std::unique_ptr<EQ::ItemData>> owned;
	std::set<int> lore;
public:
	bool dead=false;
	uint16 measured_heal_spell=0;
	uint64 healed=0,overheal=0,damage=0,heal_events=0,main_heal_events=0,damaging_hits=0;
	bool Death(Mob*,int64,uint16,EQ::skills::SkillType,KilledByTypes,bool)override{dead=true;return true;}
	void HealDamage(uint64 amount,Mob *caster=nullptr,uint16 spell=SPELL_UNKNOWN)override{
		auto before=GetHP();Client::HealDamage(amount,caster,spell);auto gain=std::max<int64>(0,GetHP()-before);
		healed+=gain;overheal+=amount-gain;++heal_events;if(spell==measured_heal_spell)++main_heal_events;
	}
	void Damage(Mob *from,int64 amount,uint16 spell,EQ::skills::SkillType skill,bool avoidable=true,int8 slot=-1,bool tick=false,eSpecialAttacks special=eSpecialAttacks::None)override{
		if(dead)return;auto before=GetHP();Client::Damage(from,amount,spell,skill,avoidable,slot,tick,special);
		auto loss=std::max<int64>(0,before-GetHP());damage+=loss;damaging_hits+=loss>0;
	}
	void pulse(){if(IsStunned()&&stunned_timer.Check())Mob::UnStun();Mob::SpellProcess();}
	bool ready(){return !casting_spell_id&&!delaytimer&&!spellend_timer.Enabled()&&!IsStunned();}
	void init(const json &c){
		class_=c["classes"][0];level=c["level"];race=base_race=c.value("race",1);auto&p=GetPP();p.class_=class_;p.level=level;p.race=race;
		p.STR=p.STA=p.AGI=p.DEX=p.INT=p.WIS=p.CHA=c.value("base_stat",100);p.hunger_level=p.thirst_level=6000;
		SetCharacterId(c.value("character_id",0));GetPTimers().SetCharID(CharacterID());LoadMulticlassMask();
		check(json(GetMulticlassList())==c["classes"],"synthetic multiclass row mismatch");
		SetClientVersion(EQ::versions::ClientVersion::RoF2);GetInv().SetInventoryVersion(EQ::versions::ClientVersion::RoF2);
		for(int k=0;k<=EQ::skills::HIGHEST_SKILL;k++){
			uint16 cap=0;for(auto cl:GetMulticlassList())cap=std::max(cap,MaxSkill(static_cast<EQ::skills::SkillType>(k),cl,level));
			if(k>=EQ::skills::SkillSpecializeAbjure&&k<=EQ::skills::SkillSpecializeEvocation&&k!=EQ::skills::SkillSpecializeAlteration)cap=std::min<uint16>(cap,50);
			p.skills[k]=cap;
		}
		p.skills[EQ::skills::SkillChanneling]=std::min<int>(p.skills[EQ::skills::SkillChanneling],c.value("channeling",200));
		SetName("FocusProbe");SetPosition(0,0,0);SetHeading(0);SaveSpellLoc();
	}
	void legal(const EQ::ItemData *i,int slot){
		check(i&&CanEquipItem(i)&&i->ReqLevel<=GetLevel(),"illegal item class/race/level");
		check((i->Slots&(1u<<slot))!=0,"illegal equipment slot");
		int key=i->LoreGroup==-1?-int(i->ID):i->LoreGroup;if(key)check(lore.insert(key).second,"duplicate lore");
	}
	void equip(const json &r,const json &policy,bool after){
		int slot=r[0];check(slot>=0&&slot<=21&&!GetInv().GetItem(slot),"duplicate/invalid slot");
		auto *i=database.GetItem(r[1]);legal(i,slot);auto copy=std::make_unique<EQ::ItemData>(*i);
		std::string key=std::to_string(i->ID);if(after&&policy.contains(key)){check(i->Focus.Effect<=0,"policy would replace existing focus");copy->Focus.Effect=policy[key];copy->Focus.Type=6;}
		EQ::ItemInstance instance(copy.get(),1);owned.push_back(std::move(copy));
		int socket=0;for(int id:r[2]){if(id){auto*a=database.GetItem(id);legal(a,slot);check(instance.IsAugmentSlotAvailable(a->AugType,socket)&&!IsAugmentRestricted(i->ItemType,a->AugRestrict),"illegal augment socket/restriction");instance.PutAugment(socket,EQ::ItemInstance(a,1));}++socket;}
		check(GetInv().PutItem(slot,instance)==slot,"inventory insert");
	}
	json purchase(const json &c){
		GetPP().aapoints=c.value("aa_budget",0);json rows=json::array();
		for(auto &id:c.value("aa_rank_ids",json::array())){
			auto*r=zone->GetAlternateAdvancementRank(id.get<uint32>());
			check(r&&r->cost>=0&&CanPurchaseAlternateAdvancementRank(r,true,true),"AA purchase gate rejected "+id.dump());
			check(SetAA(r->id,r->current_value,r->base_ability->charges),"SetAA rejected");
			GetPP().aapoints-=r->cost;GetPP().aapoints_spent+=r->cost;
			rows.push_back({{"rank",r->id},{"cost",r->cost},{"name",r->base_ability->name}});
		}
		return rows;
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
	zone=new Zone(32,0,"soldungb");zone->LoadBaseData();zone->LoadAlternateAdvancement();is_zone_loaded=true;
	json out={{"scope","Controlled timed native primary-hand attacks and native self-heal casting. No NPC AI, outgoing attack policy, regen, buffs ticking, pathing, or player acceptance. AA gate plus in-memory usable ranks, not persisted earned ownership."},{"cases",json::array()}};
	for(auto &c:input["cases"])for(bool after:{false,true}){
		seed=c.value("seed",20261120);zone->random.Reseed();EQ::Random::Instance()->Reseed();
		auto *player=new Subject();player->init(c);for(auto&r:c["slots"])player->equip(r,input["policy"],after);
		auto aa=player->purchase(c);player->CalcBonuses();entity_list.AddClient(player);
		player->SetTarget(player);player->SetHP(player->GetMaxHP());player->SetMana(player->GetMaxMana());
		int spell=c["heal_spell"];check(IsValidSpell(spell)&&player->GetSpellMinLevel(spell)<=player->GetLevel(),"illegal healing spell");player->GetPP().mem_spells[0]=spell;player->measured_heal_spell=spell;
		int base=player->CalcSpellEffectValue(spell,0,player->GetLevel(),10,player);
		json metrics={{"cast_ms",player->GetActSpellCasttime(spell,spells[spell].cast_time)},{"mana_cost_sample",player->GetActSpellCost(spell,spells[spell].mana)},{"healing_sample",NightcapHeroicCast::Cast::Deliver(true,[&]{return player->GetActSpellHealing(spell,base,player);})},
			{"hp",player->GetMaxHP()},{"mana",player->GetMaxMana()},{"heal_amount",player->GetHealAmt()},{"spell_damage",player->GetSpellDmg()},{"channeling",player->GetPP().skills[EQ::skills::SkillChanneling]}};
		const auto *type=content_db.LoadNPCTypesData(c["npc_id"]);check(type,"missing NPC");
		std::vector<Threat*> threats;std::vector<uint32> next,interval;
		for(int n=0;n<c.value("attackers",1);n++){
			auto*t=new Threat(type,nullptr,glm::vec4(0,5,0,256),GravityBehavior::Water);entity_list.AddNPC(t,false);t->SetTarget(player);t->SetAttackTimer();
			check(player->CombatRange(t),"outside melee range");auto timer=t->GetAttackTimer();auto delay=timer.GetDuration();check(delay>0,"NPC delay zero");threats.push_back(t);interval.push_back(delay);next.push_back(delay);
		}
		zone->random.Reseed();EQ::Random::Instance()->Reseed();
		uint32 start=Timer::GetCurrentTime(),duration=c.value("duration_ms",180000),retry=0,attempts=0,starts=0,swings=0,stunned_ms=0,landed_casts=0,failed_casts=0;
		uint64 receipt=0;bool pending=false;json trace=json::array();std::string result="duration";
		uint32 ms=0;
		for(;ms<=duration;ms+=10){
			for(size_t n=0;n<threats.size();n++)if(ms>=next[n]&&!threats[n]->dead&&!player->dead){threats[n]->Attack(player,EQ::invslot::slotPrimary);next[n]+=interval[n];++swings;}
			if(player->dead){result="player_death";break;}
			player->pulse();
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
		json row={{"id",c["id"]},{"stage",after?"after":"before"},{"seed",seed},{"metrics",metrics},{"aa",aa},{"spent_points",player->GetPP().aapoints_spent},{"result",result},{"elapsed_ms",std::min(ms,duration)},{"hp_end",player->GetHP()},{"mana_end",player->GetMana()},{"attempts",attempts},{"starts",starts},{"landed_casts",landed_casts},{"failed_started_casts",failed_casts},{"pending_cast",pending},{"swings",swings},{"damaging_hits",player->damaging_hits},{"damage",player->damage},{"healing",player->healed},{"overheal",player->overheal},{"stunned_ms",stunned_ms},{"npc_interval_ms",interval},{"trace",trace}};
		out["cases"].push_back(row);
		// Objects deliberately retained until process exit: no logout, corpse, save, or cleanup callbacks.
		for(auto*t:threats){t->SetTarget(nullptr);t->WipeHateList();t->SetPosition(100000+out["cases"].size()*1000,100000,0);}player->SetTarget(nullptr);
		player->SetPosition(100000+out["cases"].size()*1000,100000,0);
	}
	std::ofstream result(argv[3]);result<<out.dump(1);return 0;
}
