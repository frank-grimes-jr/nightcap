"""Record reviewed source/build/test evidence before this authorized publication."""
import hashlib
import json
from pathlib import Path
from inventory_release_support import ROOT,HERE,ART,AUTHORIZATION,save


def main():
    assert not (HERE/'native-deployment.json').exists(),'Published release: preserve observed evidence; do not replay preparation'
    build=json.loads((ART/'native-build.json').read_text())
    signed=json.loads((ART/'signed/verification.json').read_text())
    assert build['status']=='PASS' and build['baseline_reproduced']
    for name,count in [('focused-tests-final.log',16),('client-runtime-tests.log',11),('rollout-tests.log',9),('client-publisher-tests.log',21),('prior-rollout-tests.log',9)]:
        text=(ART/name).read_text(encoding='utf-8');assert 'Ran '+str(count)+' tests' in text and '\nOK' in text,(name,text[-700:])
    save(HERE/'release-checks.json',{'status':'PASS','native_build_sha256':hashlib.sha256((ART/'native-build.json').read_bytes()).hexdigest(),
        'focused_tests':16,'runtime_groups':11,'catalog_original_byte_guards':120,'wrapper_fault_tests':9,
        'retained_operator_fault_tests':9,'client_publisher_tests_windows':{'total':21,'passed':16,'posix_only_skips':5},
        'wiki_content_refresh_tests':20,'public_wiki_source_reproduced':True,
        'native_visual_acceptance':'OPEN','linux_publication_tests':'required during private stage before preflight'})
    save(HERE/'review.json',{'status':'PASS','scope':'Two independent adversarial source/release reviews; additional cross-model review declined by owner',
        'findings_resolved':['Explicit mutually exclusive label alignments',
            'Hosted verifier retains actual current Quick Buff dbstr descriptor',
            'Admission reopen requires hosted verification of the exact published channel and shipped signature',
            'Standalone publisher disabled; paired rollout owns publication under deployment/GM locks behind closed gateway'],
        'combat_mapping':{'MIT':'GetMitigationAC cached combat value','AVD':'GetTotalDefense; -1 displays Auto',
            'AC':'Conventional native client display','ATK':'GetTotalATK conventional rating','DMG':'GetSpellDmg','HEAL':'GetHealAmt'},
        'attributes':'Current/GetMax*/GetHeroic* server getters; actual cap includes heroic allowance',
        'compatibility':'NCST1 remains byte-compatible; separate negotiated NCIV1; stale/replay/identity guards',
        'scope_preserved':'No bonus, balance, schema, item/cache, quest or player-state edits. Deployed source/pair reproduced before isolated compile.',
        'native_visual_player_acceptance':'OPEN'})
    paths=['tools/client_inventory_summary_ui.py','tools/client_character_stats_ui.py',
        'tools/tests/test_client_character_stats.py','tools/tests/test_inventory_stats_protocol.py','tools/tests/test_inventory_stats_capture.py',
        'server-mods/code/common/inventory_stats_protocol.h','server-mods/code/zone/gm_commands/nightcapui.cpp',
        'server-mods/code/zone/command.cpp','server-mods/code/zone/client.h',
        'eq-client-dll/src/inventory_stats_state.h','eq-client-dll/src/ui_hooks.h','eq-client-dll/tests/equipped-stats-labels.cpp',
        'eq-client-dll/config/patch-sites.json','eq-client-dll/src/runtime_contract.h','eq-launcher/internal/preflight/catalog.json']
    save(HERE/'source-fingerprints.json',{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    save(HERE/'verification.json',{'status':'AUTHORIZED_SIGNED_CANDIDATE_NOT_DEPLOYED','owner_authorization':AUTHORIZATION,
        'native_build':'native-build.json','candidate_zone':build['binary_sha256']['candidate'],
        'baseline_zone':build['binary_sha256']['baseline'],'client':signed,'player_qa':'OPEN'})
    readme='''# Inventory combat stats, caps and heroic totals

The owner explicitly authorized the screenshot layout and live-testing publication.
Exact acceptance criteria and combat/stat sources are in SPEC.md. The November12
read-only probe confirmed heroic mechanics already active; this release changes
the display and read-only stat delivery, with no balance, item or player edits.

## Reviewed implementation and current release state

Main Inventory shows HP/MP/endurance, AC/MIT/AVD/ATK/DMG/HEAL, XP/AA XP, attributes,
resists and weight. Attributes use green current, white /actual cap and gold signed
heroics. The actual cap includes heroic allowance; heroics are a component already
included in totals. AC retains the conventional native display. MIT is the cached
combat mitigation AC; AVD is total server defense, not item mod2 Avoidance. Auto
preserves the automatic-avoidance sentinel. Ratings are not percentages or DPS.

The panel/window widen40px and extend56px, keeping normal fonts and scroll access.
Equipment/bag/button behavior and other tabs remain. The normal generator and
scoped transform use tools/client_inventory_summary_ui.py. It modifies only the
owning current Inventory controls, preserving unrelated signed XML bytes.

NCST1 and its33fields remain unchanged. Only the negotiated inventory subcommand
sends NCIV1; old clients continue stats without new frames. Identity, sequence,
8second freshness, one/sec client and3sec server throttle, silent chat and state
clearing remain. Client::RefreshEquippedStats gains only a nonvirtual parameter;
no Client member/vtable/ItemData/cache layout changes. Source-only patch applies
to retained deployed source, excluding unrelated unshipped title gameplay.

Current DoT zone7b61b5ac reproduces byte-for-byte before compiling the two affected
retained command unity units. Candidate zoneb737e641 preserves world95fc228a,
shared_memoryb60c4dfc, Quick Buff, Imitate Death, DoT ticks and all current content.
Signed client2026111202/proxy0.13.6 changes DLL/catalog/Inventory XML only;145other
descriptors/URLs, Quick Buff strings, history/tombstones and config remain.
The candidate is signed and locally verified, not yet deployed/published.

## Checks and rollout

16focused native/protocol/XML checks,11DLL runtime groups,120exact-client guards,
9new rollout gates and9retained operator fault checks pass. The Windows publisher
suite passes16with5POSIX-only skips; all21must pass in Linux before preflight.
Independent reviews resolved alignment, retained-string verification, exact hosted
receipt binding and standalone publisher bypass. Owner declined extra cross-model.
The public wiki's614files reproduce exactly; only four guides/history plus search
change,609files remain.20wiki tests pass; unrelated refresh drift stays explicit.

rollout.py inherits the current one-shot operator's deploy/GM locks, zero players,
125second closed admission drain, clean whole-runtime stop, stopped full backup,
saved-state boot model, one market rotation and preservation/failure-hold gates.
Do not kill a single production zone or replay terminal actions. Native activation
keeps admissions closed; publish-client is the only permitted publication path.
Verify the exact hosted signature/channel/assets before open. Private signing
seed never leaves the local machine. Client/wiki publication receipts will be
recorded after observing the actual outcome; planning is not deployment proof.

Recovery uses current player state and a fresh guarded prior-image transition;
never restore an old player snapshot. Client recovery needs a higher signed
counter restoring the prior matching assets while retaining newer unrelated files.

## Exact owner in-game QA

1. After publication, fully exit EQ and use normal launcher Play. Open main
   Inventory with the managed Nightcap skin. Confirm combat rows appear above XP
   and the seven attributes, using the normal font without clipping or overlap.
2. Confirm green current / white cap / yellow signed heroic for STR/STA/AGI/DEX/
   WIS/INT/CHA. +0 is legitimate with no heroics. The actual cap includes heroic
   allowance, unlike a base-only cap: never add the yellow component again.
3. With owned eligible gear, equip/remove a heroic item or legal augment, change
   shield and apply/remove ordinary stat/defense buffs. Values should update within
   the existing throttle. Bagged and training items must not supply worn bonuses.
4. MIT is the current server mitigation rating; AVD is its complete hit-check
   defense rating, separate from item Avoidance/Dodge/Shield Block. Auto denotes
   the existing automatic-avoidance effect; it is not guaranteed against every
   attack rule. DMG/HEAL are capped stat bonuses, not actual cast amounts.
5. Check ordinary and large values, low/high/zero heroics, XP/AA bars, weight,
   scroll access with saved window sizes, bags, gear drag/drop and all bottom
   buttons. Other Stats/Pet Armor/AA tabs and the single Shield Block total remain.
6. Zone, relog, change character and reload the skin. Old values must expire to
   -- while refreshing; no internal frames, target-NPC callback or log spam.

Visible player/native acceptance and broader combined-build balance remain OPEN.
'''
    (HERE/'README.md').write_text(readme,encoding='utf-8',newline='\n')
    for relative,text in [('CHANGES.md','## 2026-11-12 — Inventory combat summary and caps prepared for live testing\n\nOwner authorized screenshot layout and paired publication. Main Inventory now\ncontains combat ratings and server current/cap/heroic attributes; MIT uses cached\ncombat AC and AVD total defense, with Auto preserving the native sentinel.\nSeparate negotiated snapshot keeps old Stats clients compatible. No balance or\nplayer-state change. Current deployed source reproduces before native rebuild;\nsigned2026111202/proxy0.13.6 and scoped614-file wiki candidate are prepared.\nDeployment/publication and owner visual QA are pending. Evidence:\ndocs/releases/heroic-stats-inventory-20261112/.\n\n'),
        ('docs/status.md','## November12 — Inventory combat summary ready for authorized live testing\n\nReviewed native/server-source build and signed2026111202/proxy0.13.6 candidate\nadd front-page combat ratings, actual caps and gold heroic totals. MIT/AVD use\nthe server combat getters; mechanics and progression remain. Activation/client\nand wiki publication are pending; owner native visual acceptance stays open.\n[Release, preservation checks and exact QA](releases/heroic-stats-inventory-20261112/README.md).\n\n')]:
        path=ROOT/relative;old=path.read_text(encoding='utf-8');i=old.index('\n')+1
        path.write_text(old[:i]+'\n'+text+old[i:].lstrip('\n'),encoding='utf-8',newline='\n')
    print('Recorded authorization, reviewed proof, exact QA and pending publication state')


if __name__=='__main__':main()
