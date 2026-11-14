// Controlled dependencies for the complete native methods inserted by measure.py.
#include "common/nightcap_melee.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include <map>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using int64 = int64_t;
using int32 = int32_t;
using int16 = int16_t;
using uint32 = uint32_t;
using uint8 = uint8_t;
namespace EQ {
namespace skills {
using SkillType = int;
enum { SkillArchery=7, SkillBackstab=8, SkillHandtoHand=28, SkillOffense=33, SkillThrowing=51,
       SkillFrenzy=74, HIGHEST_SKILL=77 };
}
namespace invslot { enum { slotPrimary=13, slotSecondary=14, slotRange=11 }; }
template<class T> T Clamp(T v,T lo,T hi) {return std::clamp(v,lo,hi);}
bool ValueWithin(int v,int lo,int hi){return lo<=v && v<=hi;}
struct ItemData { uint32 ID; int Damage; };
struct ItemInstance { ItemData data; const ItemData *GetItem() const {return &data;} };
}
namespace Class {enum {Warrior=1, Paladin=3, Ranger=4, ShadowKnight=5, Monk=7, Bard=8, Rogue=9,
                       Beastlord=15, Berserker=16, WarriorGM=20, PaladinGM=22, RangerGM=23,
                       ShadowKnightGM=24, MonkGM=26, BardGM=27, RogueGM=28, BeastlordGM=34, BerserkerGM=35};}
namespace SBIndex {enum {PET_RAMPAGE_DMG_MOD, SHIELD_TARGET_MITIGATION_PERCENT};}
namespace Chat {enum {MeleeCrit};}
namespace eSpecialAttacks {enum {ChaoticStab, Rampage, AERampage};}
namespace SpecialAbility {enum {MeleeImmunity,Rampage,AreaRampage};}
namespace HeroicBonusBucket {enum {DexRangedDamage,DexMaxEndurance,DexEnduranceRegen};}
namespace NumHit {enum {OutgoingHitSuccess};}
constexpr int BOW_DOUBLE_DAMAGE=0, SPELL_UNKNOWN=65535, DMG_RIPOSTED=-3, DMG_INVULNERABLE=-5, ALL_SKILLS=-1;
constexpr int EVENT_USE_SKILL=0;
#define Log(...)
#define LogCombat(...)
#define FilteredMessageString(...) SilentMessage()
#define RuleI(section,name) Rules::name
#define RuleR(section,name) Rules::name
#define RuleB(section,name) Rules::name
namespace Rules {
constexpr double HeroicDexterityMultiplier=1, ArcheryBaseDamageBonus=1, ArcheryHitPenalty=0, LevelDifferenceRollBonus=0;
constexpr int ArcheryBonusLevelRequirement=51, PCAccuracyAvoidanceMod2Scale=100, PCAttackPowerScaling=100,
              LevelDifferenceRollCheck=-1, StunChance=0;
constexpr bool HeroicStatsUseDataBucketsToScale=false, ArcheryBonusRequiresStationary=true,
               UseMobStaticOffenseSkill=false, UseLiveRiposteMechanics=true;
bool NightcapHeroicMeleeScaling=true, ProjectileDmgOnImpact=true;
}
struct Zone {
    struct Random {
        std::mt19937 rng{1709u};
        int Roll0(int n){return n>0 ? static_cast<int>(rng()%static_cast<unsigned>(n)) : 0;}
        bool Roll(int percent){return Roll0(100)<percent;}
    } random;
} zone_instance, *zone=&zone_instance;
struct StatBonuses {
    int heroic_dex_ranged_damage=0, heroic_str_melee_damage=0, heroic_max_end=0, heroic_end_regen=0;
    int HitChance=0, Attack_Accuracy_Max_Percent=0, increase_archery=0, StrikeThrough=0;
    int Accuracy[80]{}, HitChanceEffect[80]{}, ArcheryDamageModifier=0, MeleeMitigation=0;
    int SkillDamageAmount[80]{}, SkillDamageAmount2[80]{}, PC_Pet_Rampage[2]{}, PC_Pet_AE_Rampage[2]{}, ShieldTargetSpa[2]{};
    int FrontalStunResist=0, StunResist=0;
};
struct DamageTable {int max_extra,chance,minusfactor;};
struct DamageHitInfo {int64 base_damage=0,min_damage=0,damage_done=0;int offense=0,tohit=0,hand=0,skill=0;};
struct ExtraAttackOptions {float armor_pen_percent=0;int armor_pen_flat=0;};
struct Inventory {const EQ::ItemInstance *operator[](int)const{return nullptr;}
                  const EQ::ItemInstance *GetItem(int)const{return nullptr;}};
struct Database {const EQ::ItemData *GetItem(int){return nullptr;}} database;
struct Parser {template<class... T>void EventBotMerc(T&&...){} } parser, *parse=&parser;
namespace fmt {template<class... T> int format(T&&...){return 0;}}
struct Mob {
    StatBonuses itembonuses{}, aabonuses{}, spellbonuses{};
    bool dead=false, player=true, moving=false, rooted=false, held_ranger=false;
    int primary=Class::Ranger, level=50, hdex=0, animation=0, queued_weapon=0, headshot=0;
    int64 received=0;
    Inventory m_inv;
    bool IsClient()const{return player;} bool IsNPC()const{return !player;} bool IsBot()const{return false;}
    bool IsPet()const{return false;} bool IsTempPet()const{return false;}
    bool IsOfClientBot()const{return player;} bool IsOfClientBotMerc()const{return player;}
    bool IsMulticlassMember(int c)const{return primary==c || (c==Class::Ranger && held_ranger);}
    bool HasCombatClass(uint8)const;
    bool IsWarriorClass()const;
    int GetHandToHandClass()const{return primary;} Mob* CastToNPC(){return this;} Mob* CastToClient(){return this;}
    const Mob* CastToClient()const{return this;}
    bool IsBerserk()const{return false;} int GetSkill(int)const{return 200;} int GetAccuracyRating()const{return 0;}
    int GetMobFixedWeaponSkill()const{return 200;} int GetMobFixedOffenseSkill()const{return 200;}
    int GetIntoxication()const{return 0;} int GetATK()const{return 0;} int GetPetATKBonusFromOwner()const{return 0;}
    int GetBestMeleeSkill()const{return 200;} int GetSTR()const{return 150;} int GetDEX()const{return 150;}
    int GetHeroicDEX()const{return hdex;} int GetHeroicSTR()const{return 0;} int GetLevel()const{return level;}
    int GetClass()const{return primary;} int GetTotalDefense()const{return 420;} int GetMitigationAC()const{return 260;}
    bool IsSitting()const{return false;} bool HasDied()const{return false;} bool IsAttackAllowed(Mob*)const{return true;}
    bool GetInvul()const{return false;} bool GetSpecialAbility(int)const{return false;} bool GetFeigned()const{return false;}
    bool IsMoving()const{return moving;} bool IsRooted()const{return rooted;} Inventory& GetInv(){return m_inv;}
    int64 GetWeaponDamage(Mob*, const EQ::ItemInstance* i){return i?i->data.Damage:0;}
    void SendItemAnimation(Mob*,const EQ::ItemData*,int){}
    void TryProjectileAttack(Mob*,const EQ::ItemData*,int,int dmg,const EQ::ItemInstance*,const EQ::ItemInstance*,int,float,bool){queued_weapon=dmg;}
    void AddToHateList(Mob*,int64,int){} void Damage(Mob*,int64 dmg,int,int){received=dmg;}
    template<class... T>void TryCombatProcs(T...){} template<class... T>void TryWeaponProc(T...){}
    template<class... T>void TrySkillProc(T...){} void TryCastOnSkillUse(Mob*,int){}
    bool HasSkillProcs()const{return false;} bool HasSkillProcSuccess()const{return false;}
    int CheckHeroicBonusesDataBuckets(int)const{return 0;}
    bool AvoidDamage(Mob*,DamageHitInfo&)const{return false;} void DoRiposte(Mob*){}
    bool BehindMob(Mob*,int,int)const{return false;} int GetX()const{return 0;} int GetY()const{return 0;}
    void Stun(int){} void SilentMessage(){} void MessageString(int,int){} int TryHeadShot(Mob*,int){return headshot;}
    int GetMeleeMinDamageMod_SE(int)const{return 0;} bool IsSpecialAttack(int)const{return false;}
    int TryAssassinate(Mob*,int){return 0;} int GetPositionalDmgAmt(Mob*){return 0;}
    void ApplyMeleeDamageMods(int,int64&,Mob*,ExtraAttackOptions*){} void TryCriticalHit(Mob*,DamageHitInfo&,ExtraAttackOptions*){}
    int GetSpecialAbilityParam(int,int)const{return 0;} bool IsPetOwnerOfClientBot()const{return false;}
    int GetSkillDmgTaken(int,ExtraAttackOptions*)const{return 0;} int GetPositionalDmgTaken(Mob*)const{return 0;}
    int GetPositionalDmgTakenAmt(Mob*)const{return 0;} int GetShielderID()const{return 0;}
    int GetShieldTargetMitigation()const{return 0;} void DoShieldDamageOnShielder(Mob*,int64,int){}
    void DoShieldDamageOnShielderSpellEffect(Mob*,int64,int){} void CheckNumHitsRemaining(int){}
    int compute_tohit(int); int GetTotalToHit(int,int); bool CheckHitChance(Mob*,DamageHitInfo&);
    int offense(int); double RollD20(int,int); void MeleeMitigation(Mob*,DamageHitInfo&,ExtraAttackOptions*);
    const DamageTable& GetDamageTable(bool)const; void ApplyDamageTable(DamageHitInfo&);
    int GetSkillDmgAmt(int); void SetHeroicDexBonuses(StatBonuses*);
    void DoAttack(Mob*,DamageHitInfo&,ExtraAttackOptions* = nullptr,bool=false);
#ifdef BOW_ORIGIN
    void DoAttackWithBowOrigin(Mob*,DamageHitInfo&,ExtraAttackOptions*,bool,bool);
    void CommonOutgoingHitSuccess(Mob*,DamageHitInfo&,ExtraAttackOptions*,bool);
#else
    void CommonOutgoingHitSuccess(Mob*,DamageHitInfo&,ExtraAttackOptions*);
#endif
    void DoArcheryAttackDmg(Mob*,const EQ::ItemInstance*,const EQ::ItemInstance*,int32=0,int16=0,
                            int16=0,int=0,uint32=0,uint32=0,const EQ::ItemData* =nullptr,int=0,float=0,bool=true);
};

// EXTRACTED METHODS

struct Profile {const char* name; int percent, flat, points;};
constexpr Profile profiles[] = {/* AA PROFILES */};

void measure(const std::string& scenario, Profile p, int hdex)
{
    Mob shooter, target;
    target.player=false;
    shooter.hdex=hdex;
    shooter.level=(scenario.rfind("51_",0)==0 ? 51 : 50);
    target.level=shooter.level;
    if (scenario.find("held")!=std::string::npos) {
        shooter.primary=Class::Bard;
        shooter.held_ranger=true;
    }
    if (scenario=="non_ranger") shooter.primary=Class::Bard;
    if (scenario.find("moving")!=std::string::npos) target.moving=true;
    if (scenario.find("rooted")!=std::string::npos) target.rooted=true;
    if (scenario=="npc") shooter.player=false;
    if (scenario=="headshot") shooter.headshot=1000;
    Rules::ProjectileDmgOnImpact=scenario!="immediate";
    shooter.SetHeroicDexBonuses(&shooter.itembonuses);
    shooter.aabonuses.ArcheryDamageModifier=p.percent;
    shooter.aabonuses.SkillDamageAmount[EQ::skills::SkillArchery]=p.flat;
    const EQ::ItemInstance bow{{101,30}}, arrow{{102,3}};
    zone->random.rng.seed(1709u);
    int landed=0, low=INT32_MAX, high=0, first=0;
    std::map<int,int> histogram;
    int64 total=0;
    constexpr int attempts=8192;
    for(int i=0;i<attempts;++i){
        target.received=-999;
        if(scenario=="skill_archery" || scenario=="throwing"){
            DamageHitInfo hit{};
            hit.base_damage=33;
            hit.damage_done=1;
            hit.skill=scenario=="throwing" ? EQ::skills::SkillThrowing : EQ::skills::SkillArchery;
            hit.hand=EQ::invslot::slotRange;
            hit.tohit=shooter.GetTotalToHit(hit.skill,0);
            hit.offense=shooter.offense(hit.skill);
            shooter.DoAttack(&target,hit);
            target.received=hit.damage_done;
        } else if(scenario=="scripted_bow"){
            shooter.DoArcheryAttackDmg(&target,nullptr,nullptr,33,0,0);
        } else{
            shooter.DoArcheryAttackDmg(&target,&bow,&arrow,0,0,0,0,0,0,arrow.GetItem());
        }
        if(Rules::ProjectileDmgOnImpact && shooter.queued_weapon){
            if(target.received!=-999 || shooter.queued_weapon!=33) throw std::runtime_error("invalid projectile launch");
            shooter.DoArcheryAttackDmg(&target,nullptr,nullptr,shooter.queued_weapon,0,0,0,bow.data.ID,arrow.data.ID);
        }
        if(target.received<0) throw std::runtime_error("unexpected immunity or missing delivery");
        const int damage=static_cast<int>(target.received);
        if(damage>0){
            if(!landed) first=damage;
            ++landed;
            low=std::min(low,damage);
            high=std::max(high,damage);
            total+=damage;
            if(scenario=="normal" && hdex==0 && p.points==0) ++histogram[damage];
        }
    }
    std::cout<<scenario<<','<<p.name<<','<<p.points<<','<<hdex<<','<<shooter.offense(7)<<','
             <<shooter.GetTotalToHit(7,0)<<','<<shooter.itembonuses.heroic_dex_ranged_damage<<','
             <<attempts<<','<<landed<<','<<total<<','<<low<<','<<high<<','<<first<<',';
    for(const auto& [damage,count]:histogram) std::cout<<damage<<':'<<count<<' ';
    std::cout<<'\n';
}

int main(){
    std::cout<<"scenario,profile,spent,hdex,offense,tohit,flat,attempts,landed,total,min,max,first,histogram\n";
    for(auto p:profiles)
        for(int hdex:{0,9,10,99,100,101,199,200,249,250,299,300,400})
            measure("normal",p,hdex);
    for(auto scenario:{"immediate","51_primary","51_held","51_moving","51_rooted",
                       "51_held_moving","51_held_rooted","non_ranger","headshot","npc",
                       "skill_archery","throwing","scripted_bow"})
        for(int hdex:{0,100,300})
            measure(scenario,profiles[0],hdex);
}
