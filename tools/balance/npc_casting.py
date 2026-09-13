"""Source-grounded engaged selection for solo-target nuke/heal/root/buff/dispel AI.

Caller supplies scan order (including explicit equal-priority order), readiness,
and current statuses. This is selection logic, not the complete NPC state machine.
"""


def choose_engaged_spell(spells, *, now, hp, max_hp, mana, max_mana, cooldowns,
                         active_self, target_rooted, target_feared,
                         target_dispellable, rng, heal_hp_percent=50,
                         self_chance=100, detrimental_chance=20):
    if max_hp<=0 or max_mana<0 or not 0<=hp<=max_hp or not 0<=mana<=max_mana:
        raise ValueError('Invalid NPC resource state')
    if any(s['type'] not in (1,2,4,8,32,512,1024) for s in spells):
        raise ValueError('Unimplemented NPC casting category requires explicit modeling')
    ratio=hp*100//max_hp
    mana_ok_for_nuke = max_mana==0 or mana*100>=max_mana*10

    def attempt(types, innate, chance):
        if not innate and chance<100 and rng.randint(0,100)>=chance:
            return None
        for s in spells:
            sid,kind=s['spell_id'],s['type']
            if (s['priority']==0)!=innate or kind not in types:
                continue
            low,high=s['min_hp_percent'],s['max_hp_percent']
            if kind!=2 and ((low and ratio<low) or (high and ratio>high)):
                continue
            cost=s['mana_cost']
            if cost>mana and mana!=max_mana:
                continue
            if cooldowns.get(sid,0)+rng.randint(0,4)*500>now:
                continue
            if kind==2:
                if not low<=ratio<=(high or heal_hp_percent):
                    continue
            elif kind==1024:
                if (not innate and rng.randint(0,99)>=50) or sid in active_self:
                    continue
            elif kind==1:
                if not mana_ok_for_nuke or (not innate and rng.randint(0,99)>=70):
                    continue
            elif kind==4:
                if target_rooted or target_feared or (not innate and rng.randint(0,99)>=50):
                    continue
            elif kind==512:
                if (not innate and rng.randint(0,99)>=15) or not target_dispellable:
                    continue
            # NPC DoCastSpell allows a full-mana NPC to cast an otherwise
            # unaffordable spell at zero mana cost, including zero-mana NPCs.
            return sid,0 if cost>mana and mana==max_mana else cost
        return None

    return (attempt((1,4,512),True,0)
            or attempt((1024,),True,0)
            or attempt((2,1024),False,self_chance)
            or attempt((1,4,512),False,detrimental_chance))
