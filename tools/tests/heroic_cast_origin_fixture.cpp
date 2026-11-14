#include "common/nightcap_spell_scaling.h"
#include "zone/raid_augment_delivery.h"
#include <functional>
#include <vector>
using uint32=uint32_t;
enum class CastingSlot: uint32 {Gem1=0,MaxGems=12,Ability=20,Item=22,Discipline=23,AltAbility=255};
thread_local const NightcapRaidAug::CastOrigin* NightcapRaidAug::CastOrigin::current=nullptr;
namespace NightcapSympathetic {enum class Line {Strike,Healing};}
/* SPELL BOUNDARY */
/* EFFECT METHODS */

void Mob::FinishCast(int spell_id,CastingSlot slot,bool from_casted_spell,uint32 aa_id,
                     bool isproc,uint32 inventory_slot,const std::function<void()>& deliver){
    /* FINISH BARRIER */
    /* CLASSIFY CAST */
    /* ORIGINAL RECIPIENTS */
    deliver();
}

int64 Mob::Landing(Mob* caster,int spell_id,int effect_value,int reflect_effectiveness){
    const int partial=partial_percent,buffslot=-1,i=0;
    auto& spell=spells[spell_id];
    spell.base_value[0]=effect_value;
    /* EFFECT ORIGIN */
    auto record_hp=[](NightcapSympathetic::Line,int64){};
    observed=0;
    switch(SpellEffect::CurrentHP){
        /* CURRENT HP */
    }
    return observed;
}

void sample(const std::string& scenario,int hint,int hwis){
    Mob caster,target,other,recipient2;
    constexpr int id=431, second=432;
    const uint32 invalid=0xffffffff;
    caster.sd=40;caster.ha=60;caster.hint=hint;caster.hwis=hwis;
    other.sd=40;other.ha=60;other.hint=hint;other.hwis=hwis;
    if(scenario=="pet" || scenario=="npc"){caster.kind=Mob::NPC;caster.pet=scenario=="pet";}
    spells[id]=Spell{};spells[second]=Spell{};
    fixture_rank.spell=scenario=="aa_rank_mismatch"?second:id;
    if(scenario=="unmemorized")caster.pp.mem_spells[0]=second;
    spells[id].no_heal_damage_item_mod=scenario=="opt_out";
    spells[id].is_discipline=scenario=="discipline";
    spells[id].skill_attack=scenario=="skill_aa";
    spells[id].combat=scenario=="combat_skill";
    rules["Spells:NightcapHeroicSpellScaling"]=scenario!="rule_disabled";
    int64 damage=0,healing=0;
    Mob* active_recipient=&target;
    if(scenario=="gem_critical"){caster.aabonuses.CriticalSpellChance=100;caster.aabonuses.CriticalHealChance=100;}
    if(scenario=="gem_partial")target.partial_percent=50;
    auto effects=[&](Mob& source,int spell_id,int reflect_effectiveness){
        damage=active_recipient->Landing(&source,spell_id,-100,reflect_effectiveness);
        healing=active_recipient->Landing(&source,spell_id,100,reflect_effectiveness);
    };
    auto deliver=[&](Mob& source,int spell_id,int reflect_effectiveness,bool isproc,const std::function<void()>& body){
#ifdef HEROIC_ORIGIN
        // SpellOnTarget takes ownership before nested hooks, then delivers one opportunity to SpellEffect.
        auto at_target=[&](auto* self){
            /* TARGET ORIGIN */
            if(body){body();return;}
            struct EffectBoundary{
                Mob* recipient;
                int value;
                int64 SpellEffect(Mob* caster,int id,float,int,int reflect,int,bool){return recipient->Landing(caster,id,value,reflect);}
            } bridge{active_recipient,-100}, *spelltar=&bridge;
            int spell_effectiveness=100,level_override=-1,duration_override=0;
            bool disable_buff_overwrite=false;
            auto send=[&](){
                /* DELIVER EFFECT */
            };
            damage=send();
            bridge.value=100;
            healing=send();
        };
        at_target(&source);
#else
        if(body){body();return;}
        effects(source,spell_id,reflect_effectiveness);
#endif
    };
    auto land=[&](Mob& source,int spell_id,int reflect=0,bool isproc=false){
        deliver(source,spell_id,reflect,isproc,{});
    };
    auto gem=[&](const std::function<void()>& callback){
        caster.FinishCast(id,CastingSlot::Gem1,true,0,false,invalid,callback);
    };
    auto aa=[&](bool timed,const std::function<void()>& callback){
        caster.FinishCast(id,CastingSlot::AltAbility,timed,1234,false,invalid,callback);
    };
    auto plain=[&]{land(caster,id);};
    auto two_targets=[&]{
        plain();
        auto first_damage=damage, first_heal=healing;
        active_recipient=&recipient2;
        plain();
        if(damage!=first_damage || healing!=first_heal)throw std::runtime_error("second recipient lost origin");
        active_recipient=&target;
    };
    if(scenario=="dot_hot"){
        spells[id].buff_duration=8;
        gem([&]{damage=caster.GetActDoTDamage(id,-100,&target,true);
                healing=caster.GetActSpellHealing(id,100,&target,true);});
    } else if(scenario=="proc_idle" || scenario=="proc_same_id" || scenario=="proc_different_id" || scenario=="parent_after"){
        auto nested=[&]{
            const int child=scenario=="proc_different_id"?second:id;
            caster.FinishCast(child,CastingSlot::Item,false,0,true,invalid,[&]{land(caster,child);});
        };
        if(scenario=="proc_idle")nested();
        else gem([&]{deliver(caster,id,0,false,nested);if(scenario=="parent_after")plain();});
    } else if(scenario=="group_gem"){gem(two_targets);}
    else if(scenario=="ae_aa"){aa(true,two_targets);}
    else if(scenario=="aa" || scenario=="aa_timed" || scenario=="aa_rank_mismatch" || scenario=="skill_aa"){
        aa(scenario!="aa",plain);
    } else if(scenario=="item_click" || scenario=="triggered" || scenario=="discipline" || scenario=="forged_gem" || scenario=="aa_no_rank"){
        const auto slot=scenario=="discipline"?CastingSlot::Discipline:
                        scenario=="forged_gem"?CastingSlot::Gem1:
                        scenario=="aa_no_rank"?CastingSlot::AltAbility:CastingSlot::Item;
        const uint32 inv=scenario=="item_click"?13:invalid;
        caster.FinishCast(id,slot,scenario=="item_click",0,false,inv,plain);
    } else if(scenario=="script_same_id" || scenario=="script_idle"){
        auto script=[&]{effects(caster,id,0);};
        if(scenario=="script_same_id")gem([&]{deliver(caster,id,0,false,script);});
        else script();
    } else if(scenario=="wrong_caster" || scenario=="wrong_spell"){
        gem([&]{land(scenario=="wrong_caster"?other:caster,scenario=="wrong_spell"?second:id);});
    } else if(scenario=="reflection"){
        gem([&]{land(caster,id,50);});
    } else if(scenario.find("_bolt")!=std::string::npos || scenario.find("_rain")!=std::string::npos){
        auto delivery=NightcapRaidAug::Delivery::Triggered;
        auto capture=[&]{delivery=NightcapRaidAug::CaptureDelivery(&caster,id);
#ifdef HEROIC_ORIGIN
            delivery=NightcapRaidAug::WithHeroicCast(delivery,NightcapHeroicCast::Targets::For(&caster,id));
#endif
        };
        if(scenario.find("aa_")==0)aa(true,capture);else gem(capture);
        if(scenario=="mismatched_rain")delivery=NightcapRaidAug::Delivery::Triggered;
        const auto origin=NightcapRaidAug::OnDelivery(&caster,id,delivery);
#ifdef HEROIC_ORIGIN
        if(scenario.find("_bolt")!=std::string::npos){
            NightcapHeroicCast::Cast::Deliver(NightcapRaidAug::HasHeroicCast(delivery)&&scenario!="mismatched_bolt",[&]{land(caster,id,0,true);});
        } else {
            if(scenario=="later_rain")delivery=NightcapRaidAug::Delivery::Triggered;
            NightcapHeroicCast::Targets targets(&caster,id,NightcapRaidAug::HasHeroicCast(delivery));plain();
        }
#else
        plain();
#endif
    } else if(scenario=="target_proc_same_id"){
        gem([&]{deliver(caster,id,0,false,[&]{land(caster,id,0,true);});});
    } else {
        gem(plain);
    }
    std::cout<<scenario<<','<<hint<<','<<hwis<<','<<caster.sd<<','<<caster.ha<<','<<damage<<','<<healing<<'\n';
}

int main(){
    rules["Spells:FlatItemExtraSpellAmt"]=1;rules["Spells:ItemExtraSpellAmtCalcAsPercent"]=1;
    rules["Spells:IgnoreSpellDmgLvlRestriction"]=1;rules["Spells:NightcapTHJDamageScaling"]=1;
    rules["Spells:BaseCritRatio"]=200;rules["Spells:DOTsScaleWithSpellDmg"]=1;
    rules["Spells:HOTsScaleWithHealAmt"]=1;rules["Spells:HOTBonusHealingSplitOverDuration"]=1;
    std::cout<<"scenario,hint,hwis,sd,ha,damage,healing\n";
    for(auto label:{"gem","aa","aa_timed","group_gem","ae_aa","proc_idle","proc_same_id","proc_different_id",
                    "parent_after","item_click","triggered","discipline","forged_gem","aa_no_rank",
                    "script_same_id","script_idle","wrong_caster","wrong_spell","reflection","pet","npc",
                    "dot_hot","rule_disabled","opt_out","gem_bolt","aa_bolt","gem_rain","aa_rain","mismatched_rain",
                    "mismatched_bolt","later_rain","target_proc_same_id","aa_rank_mismatch","skill_aa","combat_skill","unmemorized",
                    "gem_critical","gem_partial"})
        for(auto stats:{std::pair<int,int>{0,0},{100,0},{0,200},{100,200},{250,350}})
            sample(label,stats.first,stats.second);
}
