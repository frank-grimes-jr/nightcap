"""Attach explicit recommendations to the complete later-expansion inventory.

Named reviews are source/content assessments, not combat approval. Everything
else is conservatively deferred and marked inventory-only, never called tested.
"""
import collections
import csv
import gzip
import hashlib
import json
import re
from analyze import HERE, ROOT, Catalog, write_csv

# ability ID: disposition, candidate cap, rationale
REVIEWS = {
    938: ('keep_utility',8,'Extended-target capacity only; preserve existing free ranks. No damage/HP/regen effect.'),
    543: ('keep_utility',1,'Pet shrink only (spell27453 ChangeHeight33). Preserve MAG/BST mask; verify extra-pet targeting.'),
    3202: ('keep_control',1,'ENC Pet Discipline hold commands; preserve Animation Empathy195 rank3 prerequisite. Tactical control still needs extra-pet QA.'),
    3512: ('test_shallow_pet_defense',3,'Pet HP 1/3/5 percent. Test ranks1/2/3 at levels30/40/50 with all owned pets; cap at rank3.'),
    3818: ('test_shallow_pet_defense',3,'Pet avoidance input5/7/10; not a direct damage-reduction percentage. Test alongside existing MAG Elemental Agility268.'),
    1403: ('test_shallow_pet_defense',1,'SPA397 base100 enters owner-derived pet AC, not 100 percent damage reduction. Rank1 only for first comparison.'),
    1205: ('conditional_role_test',1,'Pet critical chance1 at rank1; postpone unless matched tests show a damage gap. Existing pet crit families can stack.'),
    3511: ('conditional_role_test',3,'Monk skill flat-damage input15/25/35; dragon-punch slot30/50/70. Historical core used rank3; not an early-level entitlement.'),
    3816: ('hold_implementation_gap',0,'Relocation spell13500 has only CHA0 in captured effect slots; no relocation handler found in reviewed source. Tooltip alone is insufficient.'),
    313: ('hold_implementation_gap',0,'Hastens relocation3816. Do not add a modifier to an unverified base action.'),
    1202: ('defer_travel_milestone',1,'Zero-mana instant long-duration self levitation changes terrain access and pulling; class-gated later convenience, not beginner necessity.'),
    1666: ('defer_travel_milestone',1,'Group levitation is more breadth than solo requires; same terrain/pulling risks as1202.'),
    1217: ('defer_travel_milestone',1,'Class-restricted Gate spell16234: mana0, cast2s, AA reuse60s. Preserve interrupts and native class identity; escape affects encounter commitment.'),
    3812: ('defer_travel_milestone',1,'Fixed-duration self invisibility, mana0/cast0.5s/reuse7s, bypasses much travel. Not a combat-damage increase but progression-affecting.'),
    291: ('defer_dependency_and_travel',0,'Requires3812 rank1 and Alaran1685 rank1, which in turn requires1684. Do not import HP grants just to backport invisibility.'),
    280: ('defer_dependency_and_travel',0,'Requires291 and1685; group convenience does not justify expanding solo list or importing Alaran chain.'),
    7002: ('defer_recovery_milestone',1,'NEC corpse recovery spell16247; requires Call to Corpse72 rank1. Reduces recovery friction but does not supply self resurrection.'),
    7007: ('defer_recovery_milestone',1,'SHD corpse recovery at600s reuse. Shared spell16247; no self-resurrection claim.'),
    3711: ('defer_recovery_milestone',1,'PAL90 percent rez of a corpse, cast6s/reuse25s. A dead solo character cannot activate it on itself.'),
    3800: ('defer_recovery_milestone',1,'CLR96 percent rez, cast3s/reuse12s. Social/recovery utility, not proof of solo survival.'),
    3705: ('defer_strong_pet_sustain',0,'Even rank1 has raw1200 HoT ticks plus melee absorb and fade recourse. Inspect scaling and recourse; inappropriate blanket early backport.'),
    3707: ('defer_strong_pet_sustain',0,'Rank1 combines avoidance, AC and10-percent melee/spell absorption with large pools. More than simple pet QoL.'),
    1580: ('defer_immunity',0,'Divine Companion Aura can erase pet-tanking risk; test aggro transfer, duration and cooldown overlap before any later release.'),
    515: ('defer_burst',0,'Rank1 gives100-percent twincast for up to10 eligible hits; combines with crit, focus and Nightcap percent spell-damage scaling.'),
    400: ('defer_burst',0,'Hastens excluded Improved Twincast515; keep unavailable while base family is deferred.'),
    133: ('defer_execute',0,'Decapitation passive skill-proc points to32336 with raw153514 nuke. Tooltip level conditions are not proof of enforcement.'),
    7703: ('defer_resource_engine',0,'Death Bloom has raw-4000HP/+2400mana periodic effects. High-level magnitude may be lethal or abusable with multiclass healing.'),
    634: ('defer_resource_engine',0,'Hastened Cannibalization compresses HP-to-mana conversion; cross-class heal loop must be measured.'),
    8347: ('defer_resource_engine',0,'Hastened Mana Draw shortens near-refill mana cooldown, especially risky with strong healer/caster unions.'),
    561: ('defer_resource_engine',0,'Hastened Harvest: keep original resource-recovery timing until sustained encounter tests pass.'),
    619: ('defer_multiclass_buff',0,'Group Pact of Wolf includes haste and triggered spell; no assumption that group utility is power-neutral.'),
    1684: ('exclude_era_grant_from_starter',0,'Free Alaran culture rank adds10 flat HP and is a dependency hub; retain explicit progression ownership instead of auto-adding to utility exceptions.'),
    1685: ('exclude_era_grant_from_starter',0,'Second free10-flat-HP Alaran rank requires1684. Later dependents need exact prerequisite decisions.'),
    1669: ('defer_duplicate_proc',0,'Knight Flurry family can add to other held-class flurry families. Budget combined extra-attack rate, not each class independently.'),
    7700: ('defer_duplicate_proc',0,'Rogue Flurry can combine with other held-class flurry/crit/skill damage.'),
    1236: ('defer_proc_burst',0,'Thunderfoot proc amplification requires exact native trigger/target tests at low level.'),
    9300: ('defer_proc_burst',0,'Massive Strike is proc damage, not a utility active button.'),
    3514: ('defer_burst',0,'Rogue Fury must be assessed with held-class haste, extra attacks and crit-damage bonuses.'),
    463: ('defer_defensive_rotation',0,'Divine Guardian can combine with other defensive/healing cooldowns; do not assume rare use in multiclass play.'),
    464: ('defer_escape',0,'Divine Peace adds threat escape; compare with existing held-class escape before adding another reset.'),
    1686: ('defer_defensive_rotation',0,'Brace for Impact introduces another mitigation layer; test uptime of the combined rotation.'),
    6488: ('defer_heal_burst',0,'Flurry of Life amplifies healer output already scaled by gear and AA; not needed to preserve baseline healing breadth.'),
    677: ('defer_burst',0,'Gift of Deathly Resolve should be tested with DoT/direct-cast triggers and twincast interactions.'),
    1662: ('defer_sustain',0,'New hybrid Spell Casting Mastery family: preserve class mask and test interactions with caster family20 on multiclass builds.'),
    3718: ('defer_duplicate_proc',0,'Additional Critical Affliction family for CLR/ENC; compare with259 where a held-class union qualifies for both.'),
}


def main():
    snap=json.load(gzip.open(HERE/'production-snapshot.json.gz','rt'))
    c=Catalog(snap['tables'])
    name_text=(ROOT/'akk-stack/code/common/spdat.h').read_text().split('namespace SpellEffect {',1)[1]
    names={int(n):k for k,n in re.findall(r'constexpr int\s+(\w+)\s*=\s*(\d+);',name_text)}
    dbstr=ROOT/'Client_RoF2_Dev/everquest_rof2/dbstr_us.txt'
    strings={}
    for line in dbstr.read_text(encoding='latin1').splitlines():
        f=line.split('^')
        if len(f)>2 and f[0].isdigit() and f[1].isdigit():
            strings[(int(f[0]),int(f[1]))]=f[2]
    rows=[]
    named=[]
    for f in csv.DictReader((HERE/'families.csv').open(encoding='utf-8-sig')):
        aid=int(f['ability_id'])
        if not int(f['post_tbs_ranks']):
            continue
        chain=c.chains[aid]
        later=[r for r in chain if r['expansion']>13]
        title=strings.get((later[0]['title_sid'],1),'')
        if aid in REVIEWS:
            decision,cap,reason=REVIEWS[aid]
            depth='named_source_content_review'
            named.append({'ability_id':aid,'name':f['name'],'decision':decision,'candidate_max_rank':cap,
                          'candidate_rank_ids':[r['id'] for r in chain[:cap]],'rationale':reason})
        else:
            cap=0
            depth='inventory_triage_not_individual_combat_review'
            if not int(f['enabled']) or int(f['grant_only']):
                decision='outside_normal_purchase_pool'
                reason='Disabled/grant-only; retain as separately reviewed system/quest progression, not a beginner purchase.'
            elif int(f['tbs_ranks']):
                decision='defer_later_ranks'
                reason='Retain only legal TBS prefix subject to older-family power caps; later increments await content progression.'
            elif not int(f['legal_open_ranks']):
                decision='hold_dependency'
                reason='No complete conservative prerequisite path; do not silently bypass missing or unpurchasable prerequisites.'
            elif not title:
                decision='hold_identity'
                reason='No first-later-rank title in reference RoF2 dbstr. Resolve signed-client identity and effects before considering a backport.'
            elif any(w in f['name'].lower() for w in ('hastened','quickened','extended','prolonged')):
                decision='defer_cooldown_duration'
                reason='Changes frequency or duration of a base ability. Audit the base and complete multiclass rotation together.'
            elif any(w in f['name'].lower() for w in ('spire','twincast','fury','wrath','destruction','flurry','thunderfoot','massive strike')):
                decision='defer_burst_or_amplifier'
                reason='Offense amplification or group burst; hold until exact stacking and encounter output are measured.'
            else:
                decision='defer_other_later_content'
                reason='No demonstrated solo capability gap requiring this backport; keep out pending individual effect/trigger and progression review.'
        eids=sorted({names.get(e['effect_id'],str(e['effect_id'])) for r in later for e in c.effects[r['id']]})
        spell=c.spells.get(later[0]['spell'],{})
        sfx='; '.join(f"{names.get(spell['effectid'+str(i)],spell['effectid'+str(i)])}={spell['effect_base_value'+str(i)]}/{spell['effect_limit_value'+str(i)]}" for i in range(1,13) if spell and spell['effectid'+str(i)] not in (254,10))
        rows.append({**f,'reference_client_title':title,'decision':decision,'candidate_max_rank':cap,
                     'review_depth':depth,'rationale':reason,'all_later_AA_effect_types':'; '.join(eids),
                     'first_later_spell_effects':sfx})
    write_csv(HERE/'later-review.csv',rows)
    (HERE/'named-exceptions-and-deferrals.json').write_text(json.dumps(named,indent=2)+'\n')
    title_coverage={}
    for label,cut in [('open',99),('tbs',13)]:
        pool,_=c.pool(cutoff=cut)
        bad=[aid for aid,ch in pool.items() if any(not strings.get((r['title_sid'],1),'').strip() for r in ch)]
        title_coverage[label]={'missing_any_retained_rank_title':len(bad),'ability_ids':bad}
    summary={'rows':len(rows),'named_reviews':len(named),'dispositions':dict(collections.Counter(r['decision'] for r in rows)),
             'reference_client_path':str(dbstr),'reference_client_sha256':hashlib.sha256(dbstr.read_bytes()).hexdigest(),
             'reference_title_coverage':title_coverage,
             'client_limit':'Reference client only; does not assert title coverage in the current signed delivered client.',
             'status':'Recommendations and deferred inventory, not deployed legality or tested combat balance.'}
    (HERE/'later-review-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='reference_title_coverage'},indent=2))


if __name__=='__main__':
    main()
