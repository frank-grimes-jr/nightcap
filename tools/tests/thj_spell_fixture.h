#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <map>
#include <string>
#include <stdexcept>
using int64=int64_t;using int32=int32_t;using int16=int16_t;using int8=int8_t;using uint16=uint16_t;
std::map<std::string,int> rules;
#define RuleB(c,n) bool(rules[#c ":" #n])
#define RuleI(c,n) rules[#c ":" #n]
namespace Class{constexpr int Wizard=12,Cleric=2;}
namespace Chat{enum{SpellCrit};}
namespace SpellEffect{enum{CriticalDotDecay,CriticalHealDecay,CriticalRegenDecay};}
namespace NightcapPetScaling{enum class CasterBonus{SpellChance,SpellDamage,DotChance,DotDamage,HealChance,HotChance};}
enum{ST_Self=6,CASTERDPS=1,SPELL_IMP_HARM_TOUCH=2774,SPELL_MANA_BURN=2751,aaSpellCastingFury,aaUnholyTouch,
 FilterSpellCrits,OTHER_CRIT_BLAST,YOU_CRIT_BLAST,OTHER_CRIT_HEAL,YOU_CRIT_HEAL,
 focusImprovedDamage,focusImprovedDamage2,focusFcDamagePctCrit,focusFcAmplifyMod,focusFcDamageAmtCrit,
 focusFcDamageAmt,focusFcDamageAmt2,focusFcAmplifyAmt,focusImprovedHeal,focusFcHealPctIncoming,
 focusFcHealPctCritIncoming,focusFcHealAmtCrit,focusFcHealAmt,focusFcHealAmtIncoming};
bool IsHarmTouchSpell(uint16){return false;}
const char* itoa(int64){return "number";}
struct Spell{int target_type=5,skill=0,override_crit_chance=0,cast_time=0,recast_time=0,recovery_time=0,buff_duration=0;
 bool good_effect=false,no_heal_damage_item_mod=false,bard=false;int classes[16];
 Spell(){std::fill(std::begin(classes),std::end(classes),1);}}spells[6000];
bool IsValidSpell(int id){return id>0&&id<6000;}
bool IsBardSong(int id){return spells[id].bard;}
struct Zone{struct Random{bool Roll(int chance){return chance>=100;}int Int(int a,int){return a;}}random;}zone_instance,*zone=&zone_instance;
struct EntityList{template<class...T>void FilteredMessageCloseString(T...){}template<class...T>void MessageCloseString(T...){} }entity_list;
struct Bonuses{int CriticalSpellChance=0,FrenziedDevastation=0,SpellCritDmgIncrease=0,SpellCritDmgIncNoStack=0,
 CriticalDoTChance=0,DotCritDmgIncrease=0,CriticalHealChance=0,CriticalHealOverTime=0;
 bool CriticalDotDecay=false,CriticalHealDecay=false,CriticalRegenDecay=false;};
struct Mob{
 Bonuses itembonuses,spellbonuses,aabonuses;enum Kind{Client,Bot,Merc,NPC}kind=Client;
 int sd=0,ha=0,hint=0,hwis=0,duration=8,level=50,cls=1;bool pet=false;
 std::map<int,int>focuses;
 bool IsClient()const{return kind==Client;}bool IsNPC()const{return kind==NPC;}bool IsBot()const{return kind==Bot;}
 bool IsMerc()const{return kind==Merc;}bool IsOfClientBot()const{return kind==Client||kind==Bot;}
 bool IsOfClientBotMerc()const{return kind!=NPC;}Mob*CastToNPC(){return this;}
 Mob*GetNightcapPetOwner()const{return pet?const_cast<Mob*>(this):nullptr;}
 int GetSpellFocusDMG(){return 0;}int GetSpellScale(){return 100;}int GetSpellFocusHeal(){return 0;}int GetHealScale(){return 100;}
 int GetSkillDmgAmt(int){return 0;}int GetClass(){return cls;}int GetLevel(){return level;}int GetAA(int){return 0;}
 int GetHeroicINT(){return hint;}int GetHeroicWIS(){return hwis;}int GetSpellDmg(){return sd;}int GetHealAmt(){return ha;}
 int GetNightcapInheritedCasterBonus(NightcapPetScaling::CasterBonus){return 0;}
 int GetFocusEffect(int focus,int,Mob* =nullptr,bool =false){return focuses[focus];}
 int GetVulnerability(Mob*,int,int,bool=false){return 0;}int GetFcDamageAmtIncoming(Mob*,int,bool=false){return 0;}
 int GetDecayEffectValue(int,int){return 0;}int CalcBuffDuration(Mob*,Mob*,int){return duration;}
 int GetHealRate(){return 0;}const char*GetName(){return "Test";}template<class...T>void MessageString(T...){}
 int64 GetActSpellDamage(uint16,int64,Mob*);int64 GetActReflectedSpellDamage(uint16,int64,int);
 int64 GetActDoTDamage(uint16,int64,Mob*,bool);int64 GetActSpellHealing(uint16,int64,Mob*,bool);
 int64 GetExtraSpellAmt(uint16,int64,int64);int32 GetNightcapRuneAmount(uint16,int32);
 int64 GetNightcapSpellDamageBonus(uint16,int64,bool=false);int64 GetNightcapHeroicSpellValue(uint16,int64,bool);
};
int checks=0;
void expect(const char*name,int64 actual,int64 expected){++checks;if(actual!=expected)throw std::runtime_error(std::string(name)+": got "+std::to_string(actual)+", expected "+std::to_string(expected));}
