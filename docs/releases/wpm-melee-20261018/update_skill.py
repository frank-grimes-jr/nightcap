"""Prepare the exact installed-knowledge patch; --apply verifies preimages."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
HEADING='## WPM melee and pet integration candidate — October 18, 2026'
OLD='## Pet and shared scaling candidate — October 18, 2026'
LOCATION=f'Source: {ROOT.as_posix()}. Current evidence: `docs/releases/wpm-melee-20261018/README.md` and `evidence/`; retained pet implementation: `docs/releases/thj-pet-scaling-20261018/IMPLEMENTATION.md`. Candidate only, not deployed or accepted in game.\n'
BLOCKS={
 'balance':'''WPM now resolves mitigation, damage tables, critical/avoidance and double/triple
attack capabilities from held classes. Six Monk attacks use Way of Steel;
the duplicate initial automated strike is removed while Master Wu stays native.
Shield Specialist reaches100%; Holy Shield is a separate shield-gated Paladin
family; Healing Light/Blessing of Life and Rage use native trigger paths.
Player and eligible-pet innate/augment attempts are independent; hostile NPC
proc policy stays native. Marr's shield adds10% received healing and successful
Mend once, not regeneration/runes. Sympathetic focuses roll individually and
select one success; disjoint VI/VII bands require paid beneficial instant heals.

Combat:NightcapHeroicMeleeScaling defaults false; staged rule true adds an
integral player weapon-hit curve (1% through100, marginal decline .0055 to1/3%).
Native flat damage/shield AC remain; pets/spells/ranged/Bash/Monk specials do not
inherit the multiplier. Holy rune230, HHE-338/400ms floor and fragment magnitudes
are explicit Nightcap calibration, not proof of THJ parity.

Shared caps750 retain Hunt headroom; permanent pets add own item SD/HA plus
min(half effective owner stat,375). Eligible earned caster crit/focus/Twinheal
transfer and percentage HA rune scaling remain. Do not silently import the
separate parity audit's proposed additive SD formula. Source: nightcap_melee.h,
attack.cpp, bonuses.cpp, effects.cpp, special_attacks.cpp and test_wpm_*.
134 combined regressions and26 native scenarios pass. Eleven checked mechanics
groups cover shield swapping, six skill timers, procs/runes and pet inheritance.
Six scenarios are class-order stat probes;20 are captured single-target encounters.
Only two seeds, no pack/raid balance certification or actual client acceptance.
Read COMPARISON.md and native-comparison.json before making balance claims.
''',
 'multiclass':'''Combined policy is1160 ranks/408 families. WPM adds Shield Specialist5,
Way of Steel2, Holy Shield30200/43210, Healing Light3, Blessing of Life3,
Rage of Rallos1/60s, Flurry12, Rapid Strikes10 and Veteran's Wrath6. Obsolete
Combat Fury309 prerequisites redirect to active earned family30 without extra
grants. Original Warrior914 remains unchanged/excluded. Allowed ranks retain
level1 purchasing, costs, prerequisites, dormant ownership and saved deadlines.
Native eligibility6960/expansion8/projection9/restore3 checks pass. Policy-approved
post-RoF2 ranks accept a full0x7ffff RoF2 profile only with client-based expansion
settings; current-era gates, partial masks, other clients and unapproved ranks
stay restricted. No stored masks or AA expansion metadata are widened.
Diagnostics also use
AA family IDs, never legacy spell_type, for cooldown readiness.

Pet depth retains Combat Stability/Agility18, Destructive Fury6, Twinheal1,
Cascade1 and reviewed pet families; only the documented two Alaran edges are
waived. Whole-roster beneficial delivery preserves native permissions/range;
support buffs coexist without additive haste. Bounded Doppelgangers use eligible
memorized/scribed spells and owner resources. Level65/PoP and389 stock additions
are staged only; no free levels, spells, points or epics. Existing general era
tools reject>50; use the paired guarded progression release, not zone-kill recipes.
''',
 'items':'''Pet content retains8 Healing/Runic Fragments,8 proc spells and33 gear changes.
WPM adds12 definitions/12 spells/20 existing gear changes: Hopebringer/Cloak
sympathetic healing, Diaku worn combat proc, extra shield sockets, Bloodfrenzy
Core power source180620, Marr shield180621 and Haste fragment180622 (+quality
offsets). Original Bloodfrenzy remains a weapon; ratios/cosmetic sockets persist.
Cursed/Tallon/Seru get distinct guarded drops988620..22, quality60/30/8/2.
Seru pet988610 and WPM988622 migrations accept the exact companion link on
retry. Unknown ID/loot namespace or case-only preimage drift fails transactionally.

Player/pet rune and healing magnitudes are calibration. Acquisition rollback
removes links only, retaining owned definitions and sockets. Never restore old
inventories, erase new-slot pet gear or remove AA definitions after purchase.
Pair schema/AA/content with rebuilt cache, world/zone and client spell/dbstr files.
Source/generators: wpm_content.py, wpm_aa.py, wpm_migration.py and pet_content.py;
real MariaDB replay, drift and recovery checks are in test_wpm_content.py.
''',
 'client':'''Permanent loadouts keep22 locations,15 Mage/eight other items and NCPA2
pages8/8/6; original slot IDs/full instances and transaction quarantine persist.
Temporary hand-ins remain separate, with native hand-conflict restoration.
Pair proxy0.11.0, Inventory/Pet Info XML, spells_us and dbstr_us with candidate
server/schema/cache/AA policy. WPM adds AA descriptions and12 proc/focus spells.
The five-file delta is unsigned/uninstalled and requires the current signed
base, including October18 travel assets. Protected reference client is read-only.
Rabid Bear benefit and Illusion: Rabid Bear are independent permanent removable
effects with normal death behavior. Real client click-off, zoning, pet lifecycle,
AA display, shield swapping and proc/HHE gameplay acceptance remain pending.
Evidence: current client-stage.json and native/unit tests, not visible QA proof.
''',
 'operations':'''Combined native candidate is isolated at/tmp/nightcap-wpm-pet-v1, derived
from retained pet/cooldown sources and the verified deployed loot successor.
Full world/zone/cache-loader hashes and source fingerprints govern pairing;
no production install occurred. Native comparisons use a separate synthetic
nightcap_wpm_balance_20261018 DB and/tmp/nightcap-balance-wpm-20261018 runtime.
No world connection or automatic DB update is allowed. Recorded gear, earned
AA spending, native clock/RNG adapters and limitations accompany results.

134 combined tests,26 native scenarios and independent WPM review pass; native
tests caught fixture item/augment eligibility and a narrow RoF2 AA expansion
compatibility gap. Source/binary/all144 linked-object fingerprints are verified.
Owner client/gameplay acceptance, signed-base reconciliation,
feature/dev/test/main promotion and guarded activation remain release gates.
New rule names require paired world/zone; regenerate matched item/spell caches.
Heroic disable/enable SQL retains exact preimages; whole-runtime OVH restart
rules still apply. Recovery preserves earned levels/AAs, deadlines, owned
definitions, stored equipment and receipts. See current ACTIVATION.md.
''',
 'wiki':'''All21 maintained guides and432 generated reward routes reviewed for the
combined candidate. Nine guides add WPM detail to the existing pet notices;
Features/home/combat/equipment/multiclass/pets/launcher/Recent changes/In development
keep explicit Not released labels. Live Classic50/caps/equipment/commands and
catalog values remain unchanged. Current wiki-review.json records exact decisions.
Thirty Linux tests, search checks and seven equipment tests pass. No publication
or unrelated global source-ledger advancement. Do not equate local generation
with public guidance or native build results with owner gameplay acceptance.
'''
}
PATHS={
 'balance':['server-mods/code/common/nightcap_melee.h','server-mods/code/zone/attack.cpp','server-mods/code/zone/bonuses.cpp','server-mods/code/zone/client_packet.cpp','server-mods/code/zone/special_attacks.cpp','tools/tests/test_wpm_combat.py','tools/tests/test_wpm_effects.py','tools/tests/test_pet_scaling.py'],
 'multiclass':['config/aa-policy.json','server-mods/code/common/nightcap_aa_policy.h','server-mods/code/zone/spell_effects.cpp','server-mods/code/zone/aa.cpp','tools/tests/verify_aa_tbs_native.py','tools/wpm_aa.py','docs/releases/wpm-melee-20261018/evidence/aa-native.json'],
 'items':['tools/wpm_content.py','tools/wpm_migration.py','tools/pet_content.py','tools/tests/test_wpm_content.py'],
 'client':['tools/client_gameplay_assets.py','docs/releases/wpm-melee-20261018/stage_client.py','docs/releases/wpm-melee-20261018/evidence/client-stage.json'],
 'operations':['docs/releases/wpm-melee-20261018/README.md','docs/releases/wpm-melee-20261018/ACTIVATION.md','docs/releases/wpm-melee-20261018/evidence/regression.json','docs/releases/wpm-melee-20261018/evidence/independent-review.json','docs/releases/wpm-melee-20261018/evidence/native-build-manifest.json','docs/releases/wpm-melee-20261018/evidence/native-pairing.json','docs/releases/wpm-melee-20261018/evidence/native-comparison.json','docs/releases/wpm-melee-20261018/COMPARISON.md','docs/status.md'],
 'wiki':['docs/releases/wpm-melee-20261018/wiki-review.json','wiki/articles/unreleased.json','wiki/content-review.json']
}


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    updates={}
    for topic,body in BLOCKS.items():
        path=SKILL/'references'/f'{topic}.md';before=path.read_text(encoding='utf-8')
        marker=HEADING if HEADING in before else OLD
        assert marker in before,topic
        start=before.index(marker);end=before.find('\n## ',start+len(marker))
        after=before[:start]+HEADING+'\n\n'+LOCATION+'\n'+body+'\n'+(before[end+1:] if end>=0 else '')
        updates[path]=(before,after)
    path=SKILL/'references/sources.json';before=path.read_text(encoding='utf-8');data=json.loads(before)
    data['observed_revisions'].pop('thj_pet_scaling_candidate_20261018',None)
    data['observed_revisions']['wpm_pet_candidate_20261018']='a8e0a91 + reviewed feature/thj-pet-scaling working tree; not deployed'
    for topic,names in PATHS.items():
        entries=data['topics'][topic]
        entries[:]=[r for r in entries if not(r['root']==ROOT.as_posix() and r['path'] in names)]
        for name in names:entries.append(dict(root=ROOT.as_posix(),path=name,role='Reviewed combined WPM/pet candidate; not deployed',revision='a8e0a91 + feature/thj-pet-scaling working tree 2026-10-18',sha256=sha((ROOT/name).read_bytes())))
    updates[path]=(before,json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    patch=''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=p.as_posix(),tofile=p.as_posix())) for p,(a,b) in updates.items())
    (HERE/'skill-update.patch').write_text(patch,encoding='utf-8')
    if args.apply:
        for path,(before,_) in updates.items():assert path.read_text(encoding='utf-8')==before,'Concurrent skill edit'
        for path,(_,after) in updates.items():path.write_text(after,encoding='utf-8')
    report={'status':'installed' if args.apply else 'prepared','files':[p.as_posix() for p in updates],
            'source_entries':sum(map(len,PATHS.values())),'deployment':'unchanged'}
    (HERE/'evidence/skill-maintenance.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
