// Deterministic boundaries for native weapon choice, physical hit submission and spell dispatch.
#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <string>
#include <vector>
using int64=int64_t; using uint64=uint64_t; using int32=int32_t; using uint32=uint32_t;
using int16=int16_t; using uint16=uint16_t; using uint8=uint8_t; using pTimerType=int;
namespace EQ {
template<class T>T Clamp(T n,T lo,T hi){return std::clamp(n,lo,hi);}
namespace skills {
using SkillType=int;
enum {SkillArchery=7,SkillBackstab=8,SkillBash=10,SkillDragonPunch=21,SkillEagleStrike=23,
      SkillDualWield=22,SkillFlyingKick=26,SkillKick=30,SkillOffense=33,SkillRoundKick=38,SkillThrowing=51,
      SkillTigerClaw=52,SkillBegging=67,SkillFrenzy=74};
int GetBaseDamage(int){return 1;} int CombatAbilityTimer(int,bool,bool){return 1;}
template<class T>bool CanUseMonkCombatAbility(const T&,int,int){return false;}
}
namespace invslot {enum {slotShoulders=6,slotFeet=19,slotHands=12,slotPrimary=13,slotSecondary=14,slotRange=11};}
namespace invaug {enum {SOCKET_BEGIN=0,SOCKET_END=5};}
namespace item {enum {ItemType1HPiercing=2,ItemTypeShield=8};}
namespace versions {enum ClientVersion {RoF2};}
struct ItemData {int ItemType=2,Slots=0x6000,AC=0,Damage=0,BackstabDmg=0; struct {int Effect=0;}Focus;const char*Name="fixture";
    bool IsType2HWeapon()const{return ItemType==1;}};
struct ItemInstance {
    ItemData data{};
    int id=0,element=0,bane=0,req=0; bool magic=false,race_ok=true,gear_ok=true;
    ItemInstance* socket=nullptr;const ItemInstance* GetAugment(int slot)const{return slot==0?socket:nullptr;}
    const ItemData* GetItem()const{return &data;}
    int GetItemArmorClass(bool)const{return 0;}
    int GetItemWeaponDamage(bool aug=false)const;
    int GetItemBackstabDamage(bool aug=false)const;
    int GetItemElementalFlag(bool)const{return element>0;}
    int GetItemElementalDamage(bool)const{return element;}
    int GetItemElementalDamage(int& mr,int&,int&,int&,int&,int&,int&,int&,int&,bool)const{mr=element;return element;}
    int GetItemBaneDamageBody(bool)const{return bane;} int GetItemBaneDamageRace(bool)const{return 0;}
    int GetItemBaneDamageBody(int type,bool)const{return type==1?bane:0;}
    int GetItemBaneDamageRace(int,bool)const{return 0;}
    int GetItemRequiredLevel(bool)const{return req;} int GetItemRecommendedLevel(bool)const{return 0;}
    bool IsClassEquipable(int)const{return gear_ok;} bool IsRaceEquipable(int)const{return race_ok;}
    bool GetItemMagical(bool)const{return magic;}
    bool IsEquipable(int slot)const{return data.Slots&(1<<slot);}
    bool IsWeapon()const{return data.ItemType!=item::ItemTypeShield;}
};
}
namespace Class {enum {Warrior=1,Ranger=4,Monk=7,Bard=8,Rogue=9,Beastlord=15,Berserker=16,MonkGM=26,BeastlordGM=34};}
namespace Race {enum {Ogre=10,Troll,Barbarian};}
namespace Chat {enum {Red,White,FocusEffect};}
enum class eSpecialAttacks {None,ChaoticStab};
namespace SpecialAbility {enum {MeleeImmunity,MagicImmunity,MeleeImmunityExceptMagical,
    MeleeImmunityExceptBane,MagicalAttack,BaneAttack};}
namespace SpellEffect {enum {SkillAttack=193};}
namespace Rules {
constexpr bool ItemExtraSkillDamageCalcAsPercent=false, BashTwoHanderUseShoulderAC=false,
               RogueBackstabHasteCorrection=false, ClassicMasterWu=false,AllowBotEquipAnyClassGear=false,
               AllowBotEquipAnyRaceGear=false,AllowFocusOnSkillDamageSpells=false;
bool BackstabIgnoresElemental=false,BackstabIgnoresBane=false;
constexpr int DoubleBackstabLevelRequirement=55,ExtraAllowedKickClassesBitmask=0,PetAttackMagicLevel=30;
constexpr float BashACBonusDivisor=25,NPCBackstabMod=3;
}
#define RuleI(group,name) Rules::name
#define RuleR(group,name) Rules::name
#define RuleB(group,name) Rules::name
constexpr int BACKSTAB_WEAPON=1, GLOWS_RED=2, SPELL_UNKNOWN=65535,DMG_INVULNERABLE=-5,
              anim1HPiercing=5,anim1HWeapon=4,animTailRake=3,animKick=2,BackstabReuseTime=10,
              BashReuseTime=8,KickReuseTime=8,FrenzyReuseTime=10;
enum {RESIST_MAGIC=1,RESIST_FIRE,RESIST_COLD,RESIST_POISON,RESIST_DISEASE,RESIST_CORRUPTION,RESIST_CHROMATIC,RESIST_PRISMATIC,RESIST_PHYSICAL};
struct Random {bool pass=true; int calls=0,element_rolls=0,element_roll=150;
    bool Roll(int){++calls;return pass;} int Roll0(int){return 0;}
    int Int(int,int maximum){if(maximum==200){++element_rolls;return element_roll;}return 0;}};
struct Zone {Random random;} zone_value,*zone=&zone_value;
struct Inv {std::array<EQ::ItemInstance*,24> slots{};EQ::ItemInstance* GetItem(int slot)const{return slots[slot];}};
struct DamageHitInfo {int64 base_damage=0,min_damage=0,damage_done=0;int offense=0,tohit=0,hand=0,skill=0;};
struct CombatAbility_Struct {int m_atk=100,m_skill=8,m_target=1;};
struct Spdat {int base_value[1]{37},limit_value[1]{},skill=8,recast_time=10,recovery_time=1;} spells[1];
struct Bonuses {int FrontalBackstabChance=0,FrontalBackstabMinDmg=0,Double_Backstab_Front=0,TripleBackstab=0;
    int DoubleSpecialAttack=0,haste=0,inhibitmelee=0,hastetype2=0,hastetype3=0,MagicWeapon=0;};
struct Timer {bool Enabled(){return false;}bool Expired(int*,int,bool){return true;} int starts=0;
              void Start(int,int){++starts;}};int database;
namespace fmt {template<class... T>int format(T...){return 0;}}
class Client;
class Mob {
public:
    int level=50,hp=100000,body=1,resistance=0,kind=0,count=0,damage=0,hate=0,
        animations=0,swings=0,attempt_procs=0,success_procs=0,on_use=0,ups=0,errors=0,doubles=0,
        last_base=0,last_skill=0,kill_after=0;
    bool behind=true,dead=false,double_ok=true,invul=false,miss=false,shield=false,dual=true;
    int class_=Class::Rogue;
    bool special[6]{}; Inv inv; Mob* target=nullptr; std::vector<int> classes{Class::Rogue};
    Bonuses itembonuses,aabonuses,spellbonuses; Timer spellend_timer,p_timers;
    eSpecialAttacks m_specialattacks=eSpecialAttacks::None;
    bool IsClient()const{return kind==0;}bool IsBot()const{return kind==1;}bool IsNPC()const{return kind==2;}
    bool IsOfClientBot()const{return !IsNPC();}Client* CastToClient();const Client* CastToClient()const;
    Mob*CastToBot(){return this;}
    Mob*CastToNPC(){return this;} Inv&GetInv(){return inv;}const Inv&GetInv()const{return inv;}
    EQ::ItemInstance* GetBotItem(int s){return inv.GetItem(s);}
    int GetHaste()const{return 100;}int GetSkill(int)const{return 200;}int GetLevel()const{return level;}
    int GetSkillDmgAmt(int)const{return 0;}int GetClass()const{return classes.front();}int GetRace()const{return 1;}
    int GetBaseRace()const{return 1;}int GetBodyType()const{return body;}int GetHP()const{return hp;}
    int GetMaxDMG()const{return 40;}int GetMinDMG()const{return 10;}int GetMinDamage()const{return 10;}
    bool HasTwoHanderEquipped()const{return false;}bool HasShieldEquipped()const{return shield;}
    bool GetInvul()const{return invul;}bool GetSpecialAbility(int n)const{return special[n];}
    bool CanEquipItem(const EQ::ItemData* i)const{for(auto x:inv.slots)if(x&&x->GetItem()==i)return x->gear_ok && x->race_ok;return false;}
    bool CanThisClassDualWield()const;bool HasSkill(int)const{return dual;}
    Bonuses* GetItemBonusesPtr(){return &itembonuses;}Bonuses* GetSpellBonusesPtr(){return &spellbonuses;}
    int CalcRecommendedLevelBonus(int,int,int value)const{return value;}
    int GetHandToHandClass()const{return GetClass();}int GetHandToHandDamage()const{return 3;}
    int GetMR()const{return resistance;}int GetCR()const{return resistance;}int GetFR()const{return resistance;}
    int GetDR()const{return resistance;}int GetPR()const{return resistance;}int GetCorrup()const{return resistance;}
    int GetPhR()const{return resistance;}int GetResist(int)const{return resistance;}
    Mob*GetOwner()const{return nullptr;}Mob*GetTarget()const{return target;}
    int GetID()const{return 1;}bool IsAttackAllowed(Mob*)const{return true;}bool CombatRange(Mob*)const{return true;}
    bool IsFeared()const{return false;}bool IsStunned()const{return false;}bool IsMezzed()const{return false;}
    bool DivineAura()const{return false;}bool HasDied()const{return hp<=0;}int ClientVersion()const{return 0;}
    bool IsMulticlassMember(int n)const{return std::find(classes.begin(),classes.end(),n)!=classes.end();}
    const std::vector<int>&GetMulticlassList()const{return classes;}int MaxSkill(int,int c,int)const{return c==Class::Rogue?200:0;}
    bool GetCombatRoundForAlerts()const{return false;}void SetCombatRoundForAlerts(){}void RaidGroupSay(const char*){}
    void MessageString(int,int id){if(id==BACKSTAB_WEAPON)++errors;}void MessageString(int,int,const char*){}
    void Message(int,const char*){}void SendColoredText(int,int){}bool BehindMob(Mob*,int,int)const{return behind;}
    int GetX()const{return 0;}int GetY()const{return 0;}bool CanFacestab()const{return false;}
    bool CheckDoubleAttack(){++doubles;return double_ok;}void CheckIncreaseSkill(int,Mob*,int){++ups;}
    void Attack(Mob*,int){++swings;}int GetSkillReuseTime(int)const{return 0;}int GetPlayerClassBit(int)const{return 0;}
    int MonkSpecialAttack(Mob*,int){return 0;}void DoAnim(int,int,bool){++animations;}
    int GetSpellFuriousBash(int)const{return 0;}int offense(int)const{return 200;}int GetTotalToHit(int,int)const{return 500;}
    void AddToHateList(Mob*,int64 h,int){hate+=static_cast<int>(h);}
    void Damage(Mob*,int64 dmg,int,int,bool=false){++count;damage+=static_cast<int>(dmg);if(kill_after==count)hp=0;}
    void TryCastOnSkillUse(Mob*,int){++on_use;}bool HasSkillProcs()const{return true;}bool HasSkillProcSuccess()const{return true;}
    void TrySkillProc(Mob*,int,int,bool landed=false){landed?++success_procs:++attempt_procs;}
    void DoAttack(Mob*,DamageHitInfo&);bool CanDoSpecialAttack(Mob* o)const{return o&&!o->invul;}
    int GetMeleeDamageMod_SE(int)const{return 0;}void SetAttackTimer(){}bool CheckDoubleRangedAttack(){return false;}
    template<class...T>bool RangedAttack(T...){return false;} template<class...T>void ThrowingAttack(T...){}
    template<class...T>void DoThrowingAttackDmg(T...){throw 1;} template<class...T>void DoArcheryAttackDmg(T...){throw 1;}
    int ResistElementalWeaponDmg(const EQ::ItemInstance*);int64 ExpectedElementalWeaponDamage(const EQ::ItemInstance*);
    int CheckBaneDamage(const EQ::ItemInstance*);
    int64 GetWeaponDamage(Mob*,const EQ::ItemInstance*,int64* =nullptr);int64 GetWeaponDamage(Mob*,const EQ::ItemData*){return 1;}
    int GetBaseSkillDamage(int,Mob* = nullptr);void RogueBackstab(Mob*,bool,int);
    void TryBackstab(Mob*,int);void DoSpecialAttackDamage(Mob*,int,int32,int32,int32,int);
    void DoSpecialAttackDamageWithBase(Mob*,int,int32,int32,int32,int,bool);
    void DoMeleeSkillAttackDmg(Mob*,int32,int,int16,int16,bool,int);void SpellSkillAttack(Mob*,int);
};
class Client: public Mob {public:void OPCombatAbility(const CombatAbility_Struct*);};
Client* Mob::CastToClient(){return static_cast<Client*>(this);}
const Client* Mob::CastToClient()const{return static_cast<const Client*>(this);}
void Mob::DoAttack(Mob*,DamageHitInfo& hit){
    last_base=static_cast<int>(hit.base_damage);last_skill=hit.skill;
    if(hit.damage_done>=0) hit.damage_done=miss?0:(m_specialattacks==eSpecialAttacks::ChaoticStab?50:hit.base_damage);
}

// NATIVE METHODS

EQ::ItemInstance weapon(int id,int damage,int backstab,int type=2){
    EQ::ItemInstance item;item.id=id;item.data.Damage=damage;item.data.BackstabDmg=backstab;item.data.ItemType=type;return item;
}

void measure(const std::string& name){
    Client player;Mob target;target.kind=2;player.target=&target;
    auto low=weapon(101,30,7),high=weapon(102,8,18),slash=weapon(103,80,70,0);
    auto socket=weapon(201,0,0);
    EQ::ItemInstance *main=&low,*off=&high;
    if(name=="swapped")std::swap(main,off);
    if(name=="tie")low.data.BackstabDmg=18;
    if(name=="only_main")off=nullptr;
    if(name=="only_off")main=nullptr;
    if(name=="slash_main")main=&slash;
    if(name=="slash_off")off=&slash;
    if(name=="neither"){main=&slash;off=nullptr;}
    if(name=="empty"){main=nullptr;off=nullptr;}
    if(name=="augmented"){socket.data.BackstabDmg=12;low.socket=&socket;}
    if(name=="weapon_fallback"){high.data.BackstabDmg=0;high.data.Damage=12;socket.data.BackstabDmg=4;socket.data.Damage=7;high.socket=&socket;}
    if(name=="explicit_ignores_weapon_aug"){socket.data.Damage=60;low.socket=&socket;}
    if(name=="required_level") high.req=51;
    if(name=="class_lock") high.gear_ok=false;
    if(name=="race_lock") high.race_ok=false;
    if(name=="offhand_slot_lock") high.data.Slots=1<<13;
    if(name=="no_dual_skill") player.dual=false;
    if(name=="twohanded_main"){slash.data.ItemType=1;main=&slash;}
    if(name=="nonmagical_main"){high.magic=true;target.special[SpecialAbility::MeleeImmunityExceptMagical]=true;}
    if(name=="nonmagical_off"){low.magic=true;target.special[SpecialAbility::MeleeImmunityExceptMagical]=true;}
    if(name=="none_magical"){target.special[SpecialAbility::MeleeImmunityExceptMagical]=true;}
    if(name=="magic_buff"){player.spellbonuses.MagicWeapon=1;target.special[SpecialAbility::MeleeImmunityExceptMagical]=true;}
    if(name.find("bane")!=std::string::npos){low.bane=16;}
    if(name=="bane_mismatch")target.body=8;
    if(name=="bane_required" || name=="bane_missing")target.special[SpecialAbility::MeleeImmunityExceptBane]=true;
    if(name=="bane_missing")target.body=8;
    if(name=="immune")target.special[SpecialAbility::MeleeImmunity]=true;
    if(name=="invulnerable")target.invul=true;
    if(name.find("element_")!=std::string::npos){low.element=30;}
    if(name=="element_high_resist")target.resistance=201;
    if(name=="element_immune")target.special[SpecialAbility::MagicImmunity]=true;
    if(name=="element_one_roll"){low.element=30;high.element=30;}
    Rules::BackstabIgnoresElemental=name=="element_ignored";
    Rules::BackstabIgnoresBane=name=="bane_ignored";
    if(name=="held_2")player.classes={Class::Bard,Class::Rogue};
    if(name=="held_3")player.classes={Class::Bard,Class::Ranger,Class::Rogue};
    if(name=="no_rogue")player.classes={Class::Bard,Class::Ranger};
    if(name=="front" || name=="chaotic" || name=="chaotic_double" || name=="seized")player.behind=false;
    if(name=="chaotic" || name=="chaotic_double")player.aabonuses.FrontalBackstabMinDmg=1;
    if(name=="chaotic_double")player.aabonuses.Double_Backstab_Front=100;
    if(name=="seized")player.aabonuses.FrontalBackstabChance=100;
    if(name.find("triple_")==0){player.aabonuses.TripleBackstab=45;}
    if(name=="triple_lost_double")player.double_ok=false;
    zone->random=Random{};
    if(name=="triple_lost_roll")zone->random.pass=false;
    if(name=="triple_death1")target.kill_after=1;
    if(name=="triple_death2")target.kill_after=2;
    if(name=="miss")player.miss=true;
    if(name=="spell_swapped")std::swap(main,off);
    if(name=="spell_empty"){main=nullptr;off=nullptr;}
    if(name=="element_uprated_low_roll")zone->random.element_roll=0;
    if(name=="resolved_zero"){
        high.data.BackstabDmg=0;high.data.Damage=0;high.magic=true;high.element=3;
        target.special[SpecialAbility::MeleeImmunityExceptMagical]=true;target.resistance=201;
    }
    if(name=="bot_primary" || name=="bot_only_off")player.kind=1;
    if(name=="bot_only_off")main=nullptr;
    if(name=="npc_unarmed"){player.kind=2;main=nullptr;off=nullptr;}
    player.inv.slots[13]=main;player.inv.slots[14]=off;
    int selected_id=0;
#ifdef STRONGER_HAND
    // A read-only diagnostic observed separately from the real packet/hit bookkeeping.
    if(player.IsClient() && name.rfind("spell_",0)!=0 && player.IsMulticlassMember(Class::Rogue)){
        auto candidate=SelectBackstabWeapon(player,&target);
        if(candidate.item)selected_id=candidate.item->id;
        assert(zone->random.element_rolls==0);
    }
#else
    if(player.IsClient() && main && main->data.ItemType==2 && player.GetClass()==Class::Rogue && name.rfind("spell_",0)!=0)selected_id=main->id;
#endif
    const auto inventory_before=player.inv.slots;
    const auto low_socket=low.socket, high_socket=high.socket;
    if(name=="generic_zero" || name=="generic_fixed")player.DoSpecialAttackDamage(&target,8,name=="generic_zero"?0:31,0,-1,10);
    else if(!player.IsClient())player.TryBackstab(&target,10);
    else if(name.rfind("spell_",0)==0)target.SpellSkillAttack(&player,0);
    else {CombatAbility_Struct packet;player.OPCombatAbility(&packet);}
    assert(player.inv.slots==inventory_before && low.socket==low_socket && high.socket==high_socket);
    std::cout<<"{\"case\":\""<<name<<"\",\"main\":"<<(main?main->id:0)<<",\"off\":"<<(off?off->id:0)
             <<",\"candidate_weapon\":"<<selected_id<<",\"hits_submitted\":"<<target.count<<",\"last_base\":"<<player.last_base
             <<",\"controlled_damage\":"<<target.damage<<",\"hate\":"<<target.hate
             <<",\"animations\":"<<player.animations<<",\"cast_on_skill\":"<<player.on_use
             <<",\"attempt_procs\":"<<player.attempt_procs<<",\"success_procs\":"<<player.success_procs
             <<",\"skill_checks\":"<<player.ups<<",\"double_checks\":"<<player.doubles
             <<",\"front_fallbacks\":"<<player.swings<<",\"equipment_errors\":"<<player.errors
             <<",\"element_rolls\":"<<zone->random.element_rolls<<",\"timer_starts\":"<<player.p_timers.starts<<"}\n";
}
int main(){
    for(auto scenario:{"standard","swapped","tie","only_main","only_off","slash_main","slash_off",
        "neither","empty","augmented","weapon_fallback","explicit_ignores_weapon_aug","required_level",
        "class_lock","race_lock","no_dual_skill","offhand_slot_lock","twohanded_main","nonmagical_main","nonmagical_off","none_magical","magic_buff",
        "bane_match","bane_mismatch","bane_required","bane_missing","bane_ignored","immune","invulnerable",
        "element_low_resist","element_high_resist","element_immune","element_ignored","element_one_roll",
        "element_uprated_low_roll","held_2","held_3","no_rogue","front","chaotic","chaotic_double","seized",
        "triple_success","triple_lost_double","triple_lost_roll","triple_death1","triple_death2","miss",
        "spell_standard","spell_swapped","spell_empty","bot_primary","bot_only_off","npc_unarmed",
        "resolved_zero","generic_zero","generic_fixed"})measure(scenario);
}
