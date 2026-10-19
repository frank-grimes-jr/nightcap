"""Prepare/apply reviewed installed knowledge, preserving concurrent topic edits."""
import argparse,difflib,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];REL=Path(__file__).resolve().parent
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
OLD='## WPM melee and pet integration candidate — October 18, 2026'
HEADING='## Combined THJ item/spell and pet/WPM candidate — October 18, 2026'
LOCATION=f'Source: {ROOT.as_posix()}. Current implementation, paired evidence and exact owner QA: `docs/releases/thj-parity-20261018/`. Companion baseline: `docs/releases/wpm-melee-20261018/`. Candidate only; no production, signing, publication or owner acceptance.\n'
BLOCKS={
'balance':'''Players and eligible permanent pets use additive effective SD for direct
damage/procs and floor(SD/2) per ordinary DoT tick, independent of duration.
Native focus/critical calculations remain; the half-SD critical contribution
uses the native ratio, an explicit Nightcap calibration. Throw Stone stays
single-additive. Hostile NPCs and disabled rules retain the legacy helper.
Clients gain0.1% per heroic INT/WIS on direct damage/healing after modifiers,
before caps. Item-mod opt-outs and reflections are covered. Heroics are
independent of the SD level gate, like focus; no DoT/HoT or owner-heroic transfer.
Both new Spells:NightcapTHJDamageScaling/NightcapHeroicSpellScaling rules default
false; reviewed candidate SQL enables them separately. Percentage healing and
HoT splitting remain. Bard runes exclude HA while instruments remain; native
Bard area-DoT dispatch is an explicit uncalibrated exception.

Preserve WPM held-class mitigation/damage/crit/double/triple-attack, six Way of
Steel attacks, earned shield/sustain AAs, independent innate/augment attempts,
Marr received-heal/Mend behavior and sympathetic-heal eligibility. Heroic STR
remains a separate switchable weapon curve. Holy rune230/HHE-338/400ms floor
and fragment magnitudes remain calibration. Shared750 caps retain Hunt headroom;
permanent pets add own SD/HA plus min(half effective owner stat,375), with eligible
earned caster AA transfer. Evaluate the combined item changes, not earlier
pet/WPM encounter results alone. Full matrix/evidence and limits are in COMPARISON.md.

Actual source-method, full-row MariaDB recovery and native tests are separately
recorded in evidence/. Matching world/zone/cache-loader and the unchanged paired
five-file NCPA2 client delta are required. Owner RoF2, pack/raid and resource
balance acceptance remain open; no cap/HP-only balancing shortcut is implied.
''',
'items':'''The exact reviewed catalog contains131 observed Ascended targets. Clean
Blood Cord/Talisman screenshots override conflicting workbook attributes;
ambiguous relocations, below-Normal fields, augmented/ambiguous identities and
unknown proc presentation are deferred. Unobserved ordinary families retain
existing policy. Normal ordinary gear stays native; intermediate values only
cap at reviewed top reductions. No universal THJ multiplier is inferred.

The209-family starter policy preserves modest quality steps below comparable
Normal dungeon gear, fixed weapon delay and cultural armor exclusion. Current
dungeon_catalog.items() emits the retuned330-definition catalog; legacy_items()
is only the dated preimage. item_scaling_overrides.py owns the final fresh
bootstrap block and requires exact present identities. The generic two-column
SD/HA planner excludes these families; never rerun destructive bootstrap live.

thj_combined_content.py composes1393 existing-item changes from full285-column
captures in one transaction. It accepts only full original, companion or final
images; drift or failed final hashes rolls back all updates. Non-gear pet/WPM
migrations use include_gear=False. Numeric recovery restores1369 rows to the
companion baseline while retaining effects/sockets for owned augments. New
acquisition recovery removes links only; never restore old inventory/AA state.
Preserve Seru's two independent new links and original loot. Fresh target
preimages, matching caches/world/zone and client spell/dbstr pairing are required.
Source/tests: thj_item_parity.py, thj_item_migration.py, thj_combined_content.py,
item_scaling_overrides.py and test_thj_*, test_item_scaling_overrides.py.
''',
'wiki':'''All21 maintained guides and432 generated reward routes are reviewed for
the combined source candidate. Eleven guides add explicit Not released item,
spell and starter/dungeon guidance, retaining the companion notices and current
live values. Features/home/Recent changes, equipment/combat/pets, starter,
upgrades/dungeons/Hunt and In development agree. Generated published rewards,
commands, acquisition and Classic50 labels remain unchanged. wiki-review.json
records each decision; check_refresh.py runs against actual HEAD/worktree.
The global source ledger is not advanced to hide drift. No local wiki edit is
published and no automated result substitutes for owner gameplay acceptance.
''',
'operations':'''The integrated candidate uses/tmp/nightcap-thj-parity-v1 and the isolated
nightcap_thj_parity_20261018 synthetic database/runtime. The completed WPM native
matrix remains a separate baseline. Pin119 requested source overlays and all
retained files/binaries/diagnostic objects using the actual build manifests;
do not infer current hashes from older worktrees. No production installation.

Existing-item changes have one full-row transaction; new-content/rules/schema
components are independently guarded, not a single multi-file transaction.
Keep writers closed through final verification in a later authorized activation.
New spell rule catalog entries require matching world and zone; regenerate
item/spell caches and use the supported full runtime restart. Formula recovery
has guarded disable/enable scripts. Numeric recovery retains pet/WPM sockets,
effects and owned state; native rollback must still represent new pet/AA data.
Classic50 remains the live profile; PoP65 is a separate complete staged profile.
Pair the unchanged unsigned five-file pet/WPM client delta with the then-current
signed base, including October18 travel assets. QA.md and ACTIVATION.md define
testing/recovery; production/main/publication and owner acceptance remain separate.
'''}
PATHS={
'balance':['server-mods/code/zone/effects.cpp','server-mods/code/zone/mob.h','server-mods/code/common/ruletypes.h','server-mods/code/common/nightcap_spell_scaling.h','tools/tests/test_thj_spell_scaling.py','tools/tests/thj_spell_fixture.h','tools/balance/native_harness.cpp','docs/releases/thj-parity-20261018/README.md','docs/releases/thj-parity-20261018/COMPARISON.md'],
'items':['config/thj-item-parity.json','tools/thj_item_parity.py','tools/thj_item_migration.py','tools/thj_combined_content.py','tools/item_scaling_overrides.py','tools/tier_spell_scaling.py','tools/starter_retune.py','tools/dungeon_catalog.py','tools/pet_content.py','tools/wpm_content.py','tools/tests/test_thj_item_parity.py','tools/tests/test_thj_combined_content.py','tools/tests/test_item_scaling_overrides.py','eq-solo-gm/scripts/tiered_loot_setup.sql','docs/releases/thj-parity-20261018/catalog-decisions.json'],
'wiki':['wiki/content-review.json','docs/releases/thj-parity-20261018/wiki-review.json','wiki/articles/unreleased.json','wiki/articles/combat.json','wiki/articles/equipment.json'],
'operations':['docs/status.md','docs/releases/thj-parity-20261018/ACTIVATION.md','docs/releases/thj-parity-20261018/QA.md','docs/releases/thj-parity-20261018/evidence/native-build-manifest.json','docs/releases/thj-parity-20261018/evidence/native-pairing.json','docs/releases/thj-parity-20261018/evidence/completion.json']}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    updates={}
    for topic,body in BLOCKS.items():
        path=SKILL/'references'/f'{topic}.md';before=path.read_text(encoding='utf-8')
        marker=HEADING if HEADING in before else OLD;assert marker in before,topic
        start=before.index(marker);end=before.find('\n## ',start+len(marker))
        updates[path]=(before,before[:start]+HEADING+'\n\n'+LOCATION+'\n'+body+'\n'+(before[end+1:] if end>=0 else ''))
    path=SKILL/'references/sources.json';before=path.read_text(encoding='utf-8');data=json.loads(before)
    revision=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()+' + reviewed feature/thj-item-spell-parity working tree'
    data['observed_revisions']['thj_item_spell_candidate_20261018']=revision+'; not deployed'
    companion=json.loads((REL/'companion-final-snapshot.json').read_text())['source'].replace('\\','/')
    for topic,names in PATHS.items():
        entries=data['topics'][topic]
        entries[:]=[r for r in entries if not(r['root'].replace('\\','/') in (ROOT.as_posix(),companion) and r['path'] in names)]
        for name in names:
            entries.append(dict(root=ROOT.as_posix(),path=name,role='Reviewed combined item/spell and pet/WPM candidate; not deployed',revision=revision,sha256=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()))
    updates[path]=(before,json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    patch=''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=p.as_posix(),tofile=p.as_posix())) for p,(a,b) in updates.items())
    (REL/'skill-update.patch').write_text(patch,encoding='utf-8')
    if args.apply:
        for p,(before,_) in updates.items():assert p.read_text(encoding='utf-8')==before,'Concurrent installed knowledge edit'
        for p,(_,after) in updates.items():p.write_text(after,encoding='utf-8')
    report={'status':'installed' if args.apply else 'prepared','files':[p.as_posix() for p in updates],
        'source_entries':sum(map(len,PATHS.values())),'source_revision':revision,'deployment':'unchanged'}
    (REL/'evidence/skill-maintenance.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':main()
