"""Exercise queued spell delivery and actual resource debits from the zone sources."""
import unittest

import test_free_trade as native


def zone(name):
    return (native.CODE / "zone" / name).read_text(encoding="utf-8")


class RaidDeliveryTests(unittest.TestCase):
    def test_projectile_impact_and_opening_rain_wave(self):
        projectile = native.body(zone("special_attacks.cpp"), "void Mob::ProjectileAttack()")
        impact = native.body(projectile, "if (ProjectileAtk[i].skill == EQ::skills::SkillConjuration)")
        queue = native.body(zone("spell_effects.cpp"), "bool Mob::TrySpellProjectile(")
        capture = next(line for line in queue.splitlines() if ".raid_delivery =" in line)
        process = native.body(zone("beacon.cpp"), "bool Beacon::Process()")
        pulse = process[process.index("const bool same_caster"):process.index(";", process.index("entity_list.AESpell(")) + 1]
        setup = native.body(zone("beacon.cpp"), "void Beacon::AELocationSpell(")
        self.assertIn("raid_delivery = NightcapRaidAug::CaptureDelivery(caster, cast_spell_id)", setup)
        native.FreeTradeTests.compile_run(self, """
#include "zone/raid_augment_delivery.h"
#include <cassert>
using namespace NightcapRaidAug;
thread_local const CastOrigin *CastOrigin::current = nullptr;
namespace EQ { namespace skills { constexpr int SkillConjuration = 1; } }
struct Spell { int resist_difficulty = 1; } spells[2];
bool IsValidSpell(int id) { return id == 1; }
struct Shot { int wpn_dmg=1, skill=1; Delivery raid_delivery=Delivery::Triggered; };
class Mob {
public:
    Shot ProjectileAtk[1];
    bool client=true;
    uint32_t id=42;
    bool IsClient() const {return client;}
    Mob *CastToClient() {return this;}
    uint32_t CharacterID() const {return id;}
    Delivery hit=Delivery::Triggered;
    void SpellOnTarget(int spell, Mob*, bool, bool, int, bool) { hit=CaptureDelivery(this,spell); }
    void Queue(int spell_id) { int slot=0;
""" + capture + """
    }
    void Impact(Mob *target) { int i=0;
""" + impact + """
    }
};
class Beacon;
struct Entities {
    void AESpell(Mob *caster, Beacon*, int spell, bool, int, int*) {
        caster->hit=CaptureDelivery(caster,spell);
    }
} entity_list;
class Beacon {
public:
    Delivery raid_delivery = Delivery::Triggered;
    uint32_t raid_caster_character_id = 42;
    int spell_id=1, resist_adjust=1, max_targets=4;
    void Pulse(Mob *caster) { const bool affect_caster=false;
""" + pulse + """
    }
};
int main() {
    Mob c, enemy; Beacon rain;
    { CastOrigin gem(&c,1,true); c.Queue(1); rain.raid_delivery=CaptureDelivery(&c,1); }
    assert(!CastOrigin::current);
    c.Impact(&enemy); assert(c.hit == Delivery::Gem && !CastOrigin::current);
    rain.Pulse(&c); assert(c.hit == Delivery::Gem && !CastOrigin::current);
    rain.Pulse(&c); assert(c.hit == Delivery::Triggered);
    { CastOrigin gem(&c,1,true); CastOrigin proc(&c,1,false,true); c.Queue(1); }
    c.Impact(&enemy); assert(c.hit == Delivery::Triggered);
    enemy.client=false;
    { CastOrigin npc(&enemy,1,false); enemy.Queue(1); }
    enemy.Impact(&c); assert(enemy.hit == Delivery::Direct);
    { CastOrigin proc(&enemy,1,false,true); enemy.Queue(1); }
    enemy.Impact(&c); assert(enemy.hit == Delivery::Triggered);
    rain.raid_delivery=Delivery::Gem; ++c.id;
    rain.Pulse(&c); assert(c.hit == Delivery::Triggered);
}
""")

    def test_prism_fizzle_jump_and_mixed_discipline_upkeep(self):
        upkeep = native.body(zone("client_process.cpp"), "void Client::DoEnduranceUpkeep()")
        jump = native.body(zone("client_packet.cpp"), "void Client::Handle_OP_Jump(")
        cast = native.body(zone("spells.cpp"), "bool Mob::DoCastSpell(")
        fizzle = cast[cast.index("const auto before = GetMana();"):cast.index("StopCasting();", cast.index("const auto before = GetMana();"))]
        native.FreeTradeTests.compile_run(self, """
#include "zone/raid_augment.h"
#include <cassert>
using uint32 = uint32_t;
using int64 = int64_t;
struct EQApplicationPacket {};
struct Spell { int endurance_upkeep=0; } spells[4];
bool IsValidSpell(int id) { return id > 0; }
namespace NightcapRaidAug {
int64_t paid=0; int events=0; bool mana_pool=false;
void Spend(Client&, int64_t cost, bool mana) { if (cost>0) { paid+=cost; ++events; mana_pool=mana; } }
bool IsExchangeSpell(uint16_t id) { return id==3; }
}
class Mob {
public:
    int64_t mana=0;
    void SetMana(int64_t n) { mana=std::max<int64_t>(0,n); }
    int64_t GetMana() const { return mana; }
};
class Client : public Mob {
public:
    NightcapRaidAug::State raid_augment;
    int64_t endurance=0;
    bool HasEndurUpkeep() const {return true;}
    void SetEndurUpkeep(bool) {}
    void TryTriggerOnCastRequirement() {}
    int GetMaxTotalSlots() const {return 3;}
    int GetLevel() const {return 50;}
    int64_t GetEndurance() const {return endurance;}
    void SetEndurance(int64_t n) {endurance=std::max<int64_t>(0,n);}
    struct Buff { int spellid=0; } buffs[3];
    uint16_t raid_direct_upkeep[3]={};
    struct Bonus { int EnduranceReduction=0; } spellbonuses,itembonuses,aabonuses;
    void BuffFadeBySlot(uint32_t i) { buffs[i].spellid=0; }
    bool IsClient() const {return true;}
    Client *CastToClient() {return this;}
    void DoEnduranceUpkeep();
    void Handle_OP_Jump(const EQApplicationPacket*);
    void Fizzle(int use_mana, uint16_t spell_id, uint32_t aa_id=0) {
""" + fizzle + """
    }
};
""" + upkeep + jump.replace("*app)", "*)") + """
int main() {
    using namespace NightcapRaidAug;
    Client c; c.raid_augment.item=Prism;
    c.mana=12; c.Fizzle(30,1); assert(paid==12 && events==1 && mana_pool && c.mana==0);
    c.mana=20; c.Fizzle(5,3); c.Fizzle(5,1,30); assert(paid==12 && events==1 && c.mana==10);
    c.endurance=18; c.Handle_OP_Jump(nullptr); assert(paid==30 && events==2 && !mana_pool);
    c.endurance=30; c.spellbonuses.EnduranceReduction=2;
    spells[1].endurance_upkeep=12; spells[2].endurance_upkeep=9; spells[3].endurance_upkeep=31;
    c.buffs[0].spellid=1; c.buffs[1].spellid=2; c.buffs[2].spellid=3;
    c.raid_direct_upkeep[0]=1; c.raid_direct_upkeep[2]=3;
    c.DoEnduranceUpkeep();
    assert(paid==40 && events==3 && c.endurance==13 && c.buffs[2].spellid==0);
}
""")


if __name__ == "__main__":
    unittest.main()
