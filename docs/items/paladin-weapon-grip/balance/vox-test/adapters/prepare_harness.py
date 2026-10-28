"""Generate fixture-only adapters. Never edits production or retained engine source."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent/'paladin-weapon-toggle'
STAGE=HERE/'harness';STAGE.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'tools/balance'))
from verify_cpp import extract_function

def replace(s,old,new):
 if s.count(old)!=1:raise ValueError('Unexpected harness anchor: '+old[:100])
 return s.replace(old,new,1)

s=(ROOT/'tools/balance/native_harness.cpp').read_text()
old='(db.at("db") != "nightcap_balance_20260912" && db.at("db") != "nightcap_wpm_balance_20261018" && db.at("db") != "nightcap_thj_parity_20261018") || db.at("username") != "nightcap_balance"'
s=replace(s,old,'db.at("db") != "nightcap_palwar_vox_20261027" || db.at("username") != "nightcap_palwar_vox"')
s=replace(s,'\t\trace = base_race = 1;\n\t\tdeity = 396;', '\t\trace = base_race = build.at("race_id").get<uint16>();\n\t\tdeity = build.at("deity_id").get<uint32>();\n\t\tgender = build.at("gender_id").get<uint8>();')
s=replace(s,'\t\tpp.race = race;', '\t\tpp.race = race; pp.gender = gender;')
s=replace(s,'\t\tstd::set<int16> worn_slots;',r'''
        fixture_block = build.value("candidate_block",0);
        fixture_weapon_id = build.at("weapon_id").get<uint32>();
        if (fixture_block < 0 || fixture_block > 3) throw std::runtime_error("Fixture block out of range");
        std::fill(std::begin(pp.spell_book),std::end(pp.spell_book),SPELL_UNKNOWN);
        std::fill(std::begin(pp.mem_spells),std::end(pp.mem_spells),SPELL_UNKNOWN);
        for (const auto &e:build.at("spellbook")) {
            const size_t slot=e.at("slot_id").get<size_t>();
            if(slot>=std::size(pp.spell_book)) throw std::runtime_error("Bad book slot");
            pp.spell_book[slot]=e.at("spell_id").get<uint32>();
        }
        for (const auto &e:build.at("memmed")) {
            const size_t slot=e.at("slot_id").get<size_t>();
            if(slot>=std::size(pp.mem_spells)) throw std::runtime_error("Bad gem slot");
            pp.mem_spells[slot]=e.at("spell_id").get<uint32>();
        }
        std::set<int16> worn_slots;''')
s=replace(s,'\t\t\tcheck_lore(item->GetItem());',r'''
            item->SetCustomDataString(entry.value("custom_data",std::string()));
            if(entry.contains("test_override")) {
                if(slot!=13 || id!=fixture_weapon_id) throw std::runtime_error("Override outside primary weapon");
                auto *p=const_cast<EQ::ItemData*>(item->GetItem());
                if(p==database.GetItem(id)) throw std::runtime_error("Attempted shared-cache mutation");
                const auto &o=entry.at("test_override");
                p->Damage=o.at("damage").get<uint32>();p->Delay=o.at("delay").get<uint8>();
                p->Accuracy=o.at("accuracy").get<int8>();
                if(o.contains("mana"))p->Mana=o.at("mana").get<int32>();
                if(o.contains("astr"))p->AStr=o.at("astr").get<int8>();
                if(o.contains("awis"))p->AWis=o.at("awis").get<int8>();
                if(o.contains("heroic_str"))p->HeroicStr=o.at("heroic_str").get<int32>();
                if(o.contains("heroic_wis"))p->HeroicWis=o.at("heroic_wis").get<int32>();
                if(o.contains("healamt"))p->HealAmt=o.at("healamt").get<int32>();
                if(o.contains("spelldmg"))p->SpellDmg=o.at("spelldmg").get<int32>();
                if(o.contains("proclevel2"))p->Proc.Level2=o.at("proclevel2").get<uint8>();
            }
            check_lore(item->GetItem());''')
old=extract_function(s,'void ConfigureSkills(')
new=r'''void ConfigureSkills(const json &build)
    {
        auto &pp=GetPP();std::fill(std::begin(pp.skills),std::end(pp.skills),0);
        for(const auto &e:build.at("saved_skills")) {
            const auto skill=e.at("skill_id").get<size_t>();
            if(skill>=std::size(pp.skills)) throw std::runtime_error("Bad saved skill");
            pp.skills[skill]=e.at("value").get<uint32>();
        }
        if(build.value("equalize_2hs",false)) pp.skills[3]=pp.skills[1];
        database.LoadBuffs(this);
        CalcBonuses();
        ApplyWeaponsStance();
        CalcBonuses();
    }'''
s=replace(s,old,new)
old=extract_function(s,'json Purchase(')
new=r'''json Purchase(const json &build)
    {
        GetPP().aapoints=build.at("saved_aa_points").get<uint32>();
        GetPP().aapoints_spent=build.at("saved_aa_spent").get<uint32>();
        if(!database.LoadAlternateAdvancement(this)) throw std::runtime_error("Native owned-AA load failed");
        json loaded=json::array();
        for(const auto &r:build.at("saved_aa")) {
            auto id=r.at("aa_id").get<uint32>();
            if(GetEarnedAACount(id)!=r.at("aa_value").get<uint32>()) throw std::runtime_error("Earned AA mismatch");
            uint32 charges=0;auto active=GetAA(id,&charges);
            loaded.push_back({{"first_rank",id},{"earned",GetEarnedAACount(id)},{"active",active},{"active_charges",charges},{"saved_charges",r.at("charges")}});
        }
        CalcBonuses();return loaded;
    }'''
s=replace(s,old,new)
extra=r'''
    int fixture_block=0;
    uint32 fixture_weapon_id=0;
    void CalcBonuses() override {
        Client::CalcBonuses();
        const auto *weapon=GetInv().GetItem(EQ::invslot::slotPrimary);
        if(fixture_block && weapon && weapon->GetID()==fixture_weapon_id && weapon->GetItem()->ItemType==0 && HasShieldEquipped())
            itembonuses.ShieldBlock+=fixture_block;
    }
    json FixtureState() {
        json equipment=json::array(),buffs_out=json::array();
        for(int slot=0;slot<=21;++slot)if(const auto *i=GetInv().GetItem(slot)){
            const auto*p=i->GetItem();
            equipment.push_back({{"slot",slot},{"id",i->GetID()},{"type",p->ItemType},{"damage",p->Damage},{"delay",p->Delay},
              {"accuracy",p->Accuracy},{"healamt",p->HealAmt},{"spelldmg",p->SpellDmg},{"heroic_str",p->HeroicStr},{"heroic_wis",p->HeroicWis},
              {"mana",p->Mana},{"astr",p->AStr},{"awis",p->AWis},{"proceffect",p->Proc.Effect},{"proctype",p->Proc.Type},{"proclevel2",p->Proc.Level2}});
        }
        for(int n=0;n<GetMaxBuffSlots();++n){const auto &b=GetBuffs()[n];if(IsValidSpell(b.spellid))buffs_out.push_back({{"slot",n},{"spell",b.spellid},{"ticks",b.ticsremaining},{"casterlevel",b.casterlevel}});}
        return {{"race",GetRace()},{"deity",GetDeity()},{"gender",GetGender()},{"size",GetSize()},
            {"classes",GetMulticlassList()},{"shield",HasShieldEquipped()},{"item_accuracy",itembonuses.HitChance},
            {"item_block",itembonuses.ShieldBlock},{"aa_block",aabonuses.ShieldBlock},{"spell_block",spellbonuses.ShieldBlock},
            {"shield_damage_aa",aabonuses.ShieldEquipDmgMod},{"equipment",equipment},{"buffs",buffs_out},
            {"skills",std::vector<uint32>(std::begin(GetPP().skills),std::end(GetPP().skills))}};
    }
'''
s=replace(s,'class BalanceClient : public Client {\npublic:', 'class BalanceClient : public Client {\npublic:'+extra)
s=replace(s,'\t\t\tc->ConfigureSkills(build);','''\t\t\tc->ConfigureSkills(build);
            c->ChangeSize(GetRaceGenderDefaultHeight(c->GetRace(),c->GetGender()),true);
            const auto once=c->FixtureState();c->CalcBonuses();
            if(once!=c->FixtureState())throw std::runtime_error("Bonus recalculation changed fixture");''')
s=replace(s,'\t\t\toutput["builds"].back()["skill_model"] = "Maximum held-class trained caps with native specialization/AA cap rules; attainability requires QA";', '\t\t\toutput["builds"].back()["fixture_state"] = c->FixtureState();\n\t\t\toutput["builds"].back()["skill_model"] = "Captured skills; optional equalization changes only starting 2HS; native skill learning retained";')
s=replace(s,'\t\t\tif (runtime) { output["native_rng_seed"]', '\t\t\toutput["builds"].back()["final_fixture_state"] = c->FixtureState();\n\t\t\tif (runtime) { output["native_rng_seed"]')
s=replace(s,'#include "common/item_instance.h"','#include "common/item_instance.h"\n#include "common/races.h"')
s=replace(s,'Native equipped-stat diagnostic; explicitly supplied AA purchases, no active buffs','Native Palwar snapshot diagnostic; saved earned AA ownership, eight captured buffs, explicit candidate item projection')
s=replace(s,'build.at("profile") == "war-clr-mnk"\n\t\t\t\t\t\t&& build.at("classes") == json::array({1,2,7})','build.at("level") == 45\n\t\t\t\t\t\t&& build.at("classes") == json::array({3,1,7})')
s=replace(s,'if (runtime) { output["native_rng_seed"] = std::stoull(std::getenv("NIGHTCAP_BALANCE_RNG_SEED")); }','if (runtime) { output["native_rng_seed"] = std::stoull(std::getenv("NIGHTCAP_BALANCE_RNG_SEED")); output["native_seed_hook_calls"] = balance_seed_calls.load(); if (!balance_seed_calls.load()) throw std::runtime_error("Native RNG seed hook unused"); }')
(STAGE/'native_harness.cpp').write_text(s)

s=(ROOT/'tools/balance/native_runtime.cpp').read_text()
s=replace(s,'#include "common/ptimer.h"','#include "common/ptimer.h"\n#include "common/races.h"')
split=s.index('json NightcapBalanceEncounter(');prefix=s[:split];s=s[split:]
s=replace(s,'c->SetName("BalanceFighter"); c->ChangeSize(6,true);','c->SetName("PalwarFixture"); c->ChangeSize(GetRaceGenderDefaultHeight(c->GetRace(),c->GetGender()),true);')
s=replace(s,'c->SetHP(c->GetMaxHP()); c->Mob::SetMana(c->GetMaxMana());\n\tentity_list.AddClient(c);','c->SetHP(c->GetMaxHP()); c->Mob::SetMana(c->GetMaxMana()); c->SetEndurance(c->GetMaxEndurance());\n\tentity_list.AddClient(c);')
s=replace(s,'const uint16 heal = c->GetSpellMinLevel(9) <= c->GetLevel() ? 9 : 15;', 'const uint16 heal = input.at("healing_spell").get<uint16>();\n\tif (c->FindSpellBookSlotBySpellID(heal) < 0) throw std::runtime_error("Unlearned fixture healing spell");')
s=replace(s,'movement.Step(c,npc,stream,50);','movement.Step(c,npc,stream,50,0,heal);')
s=replace(s,'const bool request_mend = wpm && !moving','const bool request_mend = (wpm || input.value("use_mend",false)) && !moving')
s=replace(s,'const int duration = input.value("duration_ms",120000);','const int duration = input.value("duration_ms",120000);\n\tconst uint32 pulse=input.value("pulse_ms",32U);\n\tif(pulse!=32 && pulse!=50) throw std::runtime_error("Unsupported timestep");')
s=replace(s,'for (uint32 ms = combat_start + 50; ms <= combat_start + duration && terminal.empty(); ms += 50)', 'uint32 last_sample=combat_start;\n\tfor (uint32 ms = combat_start + pulse; ms <= combat_start + duration && terminal.empty(); ms += pulse)')
s=replace(s,'\t\tAdvance(50);','\t\tAdvance(pulse);')
s=replace(s,'movement.Step(c,npc,stream,50,0,heal);','movement.Step(c,npc,stream,pulse,0,heal);')
s=replace(s,'if ((ms-combat_start) % 500 == 0) { sample(); }','if (ms-last_sample >= 500) { sample(); last_sample=ms; }')
s=replace(s,'json result = {{"npc_id",npc_id},{"player_entity_id",c->GetID()}', 'sample();\n\tjson result = {{"pulse_ms",pulse},{"npc_id",npc_id},{"player_entity_id",c->GetID()}')
s=replace(s,'Native held-class melee and self-heal controller; packet combat skills, candidate gear and earned-AA purchases; not final balance certification','Native Palwar snapshot melee/self-heal controller; saved earned AAs, captured buffs, native Monk buttons/Mend; candidate-only gear, single Vox, no raid adds or optimized activated-AA rotation')
(STAGE/'native_runtime.cpp').write_text(prefix+s)
for name in ['native_runtime.h','build_native.py']:(STAGE/name).write_bytes((ROOT/'tools/balance'/name).read_bytes())
receipt={'scope':'Fixture-only adapters; retain original IDs, copy-owned item definitions, source engine combat unchanged','sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in STAGE.iterdir() if p.is_file()}}
(HERE/'harness-preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Prepared isolated adapters:',STAGE)
