"""Maintain reviewed installed knowledge after verified activation/publication."""
import argparse,difflib,hashlib,json,re,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    deployed=json.loads((OUT/'production-verification.json').read_text())
    client=json.loads((OUT/'client-public-verification.json').read_text())
    wiki=json.loads((OUT/'wiki-publication.json').read_text())
    assert deployed['gateway_open'] and deployed['content_installed'] and not deployed['database_restored']
    assert client['release']==2026110701 and client['hosted'] and wiki['result']=='PASS'
    names=['SKILL.md']+['references/'+n+'.md' for n in ('world','items','client','operations','balance','wiki')]+['references/sources.json']
    before={n:(SKILL/n).read_text(encoding='utf-8') for n in names};after=dict(before)
    route='E:/EQ_Local_Dev/_worktrees/adventure-journal-endgame'
    world='''Adventure Journal / Epic0.5 is now **The Last Lantern**, deployed November7 for
live QA; normal-player acceptance remains OPEN. See docs/adventure-journal/
release-20261107/{README.md,production-verification.json,CAMPAIGN-QA.md} in
ROOT. Twelve chapters per playthrough use16Task definitions9500–9515,
64activities, three shared chapters and one of five optional oath paths, then
eight continuations through50. Six public companions/couriers complement eight
private company memories in version80 (Unrest, LowerGuk, SolB, CT, Hole, Fear,
original Hate76 twice). Existing Keeper186 runs/rewards remain separate.
Native completed_tasks, not another story mask, authorizes progression, claims
and charm powers. Campaign completion saves before deleting its active checkpoint;
failed native SQL acknowledgements retain dirty flags/history retries. Private
UUID/start/version/membership, live prerequisites, ordered wave counts, range and
the normalized pet/swarm killer's current native party fence combat credit.
Transient actors grant no XP/loot/checklist/corpse-state reward and reset on retry.
The independent return companion survives attempt cleanup. New spawn2 points are
created by the retained saved-state loader without deleting unrelated snapshots.
Chronicler999220 in EastCommonlands22 starts at20; Oren998901 handles eight armor
slots (two wrists share a visible region). Four legal fits and40/46/final50 earned
refits use items964000–964127;900620 remains the existing Reforging Box. Only100
armor definitions are reachable; do not publish unused lower grades as rewards.
Stable character/slot UUID receipts freeze first claims. Missing receipted gear
does not yield free replacements. Same-slot refits CAS the complete inventory row,
GUID, ownership and operation receipt in one InnoDB transaction, preserving augments,
custom dye, binding and ornaments. Uncertain commit acknowledgements quarantine;
inspect receipts and recover forward. A pending fit made illegal by class release
needs offline operator review, not another freely mutable reservation.
Item900501 and spells42800–42805 retain bounded powers and600second shared cooldown.
Attunement/click also require durable native history; legacy Perl forge cannot mint
an unreceipted charm. Pair native Epic05Contract, three plugins, item script, public
bindings, all16Tasks, control tables, effective item policy and signed2026110701.
World/zone/shared-memory links reproduce current shipping baselines before changes.
The new cache validates128armor afterimages and preserves every unrelated native
item/spell record. Keep this personal-item policy after any claim; never restore
old player snapshots or use an older FreeTrade cache generator for recovery.
Full normal-account scenes, oath paths, group/pet/SSF, pathing, brand mechanics,
race/gender armor appearance and combined balance remain separate player QA.
Source: last_lantern.inc, last_lantern_{policy,scene_policy,inventory,catalog}.h,
task_{manager,client_state}.cpp, advanced_loot_inventory.cpp, epic05{,_store}.pl.
Tests: test_lantern_*; real MariaDB refit/SQL/24DBI controls;53quest assertions.
'''.replace('ROOT',route)
    text=after['references/world.md'];start=text.index('Adventure Journal / Epic 0.5 remains an **unreleased eight-task candidate**;')
    end=text.find('\n\n',start);end=len(text) if end<0 else end
    after['references/world.md']=text[:start]+world.rstrip()+text[end:]
    sections={
      'items':'''Eight personal Last Lantern pieces/four fits use964000–964127;100variants
are reachable. Effective policy runs AFTER global FreeTrade: no trade/transfer/pet,
zero resale, permanent, no attuning/LORE workaround. Current FVNoDropFlag=0 is a
reviewed invariant; global FV bypass changes require another route audit. Refit
preserves all saved instance metadata/GUID and only updates default colors, not
custom dye. Stable first-claim UUID + complete inventory CAS/ownership/operation
receipt prevent cloning and uncertain retries. Keep new cache/native consumers
during forward recovery; never restore stale inventories. Source common/
last_lantern_{policy,inventory}.h and zone/advanced_loot_inventory.cpp; real
MariaDB rollback/replay/lost-ack and metadata controls in release-20261107/.
Normal dungeon-derived budgets, one type22socket on six major pieces, none on
wrists, no haste/heroics/focus/set bonus. Rendering and full balance QA stay open.''',
      'client':'''Signed game2026110701 adds six oath spell rows and one client-note entry
containing six campaign changes. Retains proxy0.13.5, current catalog,147asset
descriptors/URLs and all38previous notes;148HTTPS files, production signature and
actual executable/proxy/catalog pair verify. Exit EQ and use normal Play. No
launcher minimum bump, desktop-channel or installed/protected client write.
Native world/zone/shared-memory and generated cache are the reviewed pair.
Actual race/gender armor rendering remains unaccepted; model/material IDs alone
are not visible-player QA. Evidence docs/adventure-journal/release-20261107/.''',
      'operations':'''Owner explicitly authorized main/server and client notes for this release.
Use docs/adventure-journal/release-20261107/rollout.py and its exact package/receipts,
not an old zone-only operator. Preflight cloned only public definitions into a
named isolated schema, rehearsed the actual signed client and verified every
unrelated cached item/spell record. Activation uses deployment/GM locks, zero
native players, closed gateway plus125second auth drain, clean supervised shutdown,
stopped full backup, exact saved-state boot-expiry model and one market rotation.
Three native binaries + owned quest bindings/content/cache are paired; old login,
UCS, supervisor, rules, existing content and player data remain. Failure holds
admissions. After content installation or claims, recover forward with the personal
item policy and receipts; never restore an old player snapshot. Main deployment
does not complete normal-player campaign/rendering/balance acceptance.''',
      'balance':'''32native earned-gear runs calibrate Last Lantern scene tiers, uninterrupted
three-wave resource use, three seeds and W/P/M, W/Cl/Wiz, W/Cl/Mnk finales.
Fresh controls buy48–98explicit level-legal AA; developed control spends500.
Pre-final builds wear seven Restored pieces and a Normal chest; support gear is
current Normal, no augments, pets or preparation buffs. Caster control uses its
Normal two-handed staff. Draft400kHP/450–900damage boss failed; final6000HP/50–110
damage plus avoided/stunned brand preserves a story challenge below raid loot.
Keep measured failures and assumptions: arena controls are not pathing, guardian,
brand, all-class or whole-expedition certification. Actual live QA remains open.
Source tools/last_lantern_balance.py and release-20261107/balance/{calibration.json,
draft-calibration.json,native-build-manifest.json}; never infer optimal builds.''',
      'wiki':'''Wiki20261107-last-lantern-v1 is published after the paired campaign/client
release. Reproduced all510previous public files from the authenticated current
source before scoped changes;613public files now include103new pages. Reviewed
all42authored articles, generated directories, acquisition/catalog values and
release labels. New guide + separate100reachable armor variants/charm directory;
Features/Home/equipment/tunnel/travel/In development/Change Log and seven zone
contexts updated. Hunt values, loot finder sources and unrelated guides retained.
All public manifest hashes, private denials, security headers and pointer rollback
verify in release-20261107/wiki-* evidence. Global unrelated source drift remains
REVIEW REQUIRED; no blind ledger advance. Browser visual QA is explicitly
unverified: no browser connector and native app approval timeout. Normal-player
armor and campaign acceptance remain OPEN; status is Live testing.'''
    }
    for topic,body in sections.items():
        name='references/'+topic+'.md';text=after[name]
        if topic=='wiki':
            text=re.sub(r'## Adventure Journal endgame — November6 unpublished design proposal\n.*?(?=\n## )','',text,flags=re.S)
        heading='## Last Lantern — November7 paired release for live QA'
        text=text.split('\n',1)[0]+'\n\n'+heading+'\n\n'+body+'\n'+text.split('\n',1)[1]
        after[name]=text
    after['references/balance.md']=after['references/balance.md'].replace('Adventure Journal/Epic 0.5 and portions of combat/item and living-economy work are candidates;','The Last Lantern has its November7 live-QA release boundary; portions of combat/item and living-economy work remain candidates;')
    after['SKILL.md']=after['SKILL.md'].replace('Tunnel NPCs, travel, waypoints, instances, Perl bindings','Tunnel NPCs, travel, instances, Adventure Journal, Perl bindings')
    sources=json.loads(after['references/sources.json']);rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    paths={
      'world':['server-mods/code/zone/last_lantern.inc','server-mods/code/zone/dungeon_service.cpp','server-mods/code/zone/dungeon_service.h','server-mods/code/zone/highkeep_rescue.inc','server-mods/code/zone/spawn2.cpp','server-mods/code/zone/attack.cpp','tools/epic05.py','tools/tests/test_lantern_runtime.py','tools/tests/test_lantern_task_save.py','server-mods/code/common/last_lantern_scene_policy.h','server-mods/code/common/last_lantern_catalog.h','server-mods/code/zone/task_manager.cpp','server-mods/code/zone/task_client_state.cpp','server-mods/plugins/epic05.pl','server-mods/plugins/epic05_store.pl','docs/adventure-journal/CAMPAIGN.md','docs/adventure-journal/SPEC.md','docs/adventure-journal/catalog.json','docs/lore/structure.md','docs/adventure-journal/release-20261107/production-verification.json'],
      'items':['server-mods/code/common/shareddb.cpp','server-mods/code/zone/pets.cpp','server-mods/code/zone/advanced_loot_inventory.h','tools/tests/rehearse_last_lantern.py','docs/adventure-journal/release-20261107/cache-private-validation.json','server-mods/code/common/last_lantern_policy.h','server-mods/code/common/last_lantern_inventory.h','server-mods/code/zone/advanced_loot_inventory.cpp','docs/adventure-journal/last-lantern-catalog.json','docs/adventure-journal/release-20261107/database-rehearsal.json'],
      'client':['eq-launcher/patch-notes.json','docs/adventure-journal/release-20261107/client-public-verification.json'],
      'operations':['docs/adventure-journal/release-20261107/rollout.py','docs/adventure-journal/release-20261107/production-verification.json','docs/adventure-journal/release-20261107/native-build.json'],
      'balance':['tools/last_lantern_balance.py','docs/adventure-journal/release-20261107/balance/calibration.json','docs/adventure-journal/release-20261107/balance/native-build-manifest.json'],
      'wiki':['wiki/catalog.py','wiki/articles/features.json','wiki/articles/index.json','wiki/articles/tunnel.json','wiki/articles/travel.json','wiki/articles/equipment.json','wiki/articles/adventure-journal.json','wiki/last-lantern-catalog.json','wiki/last_lantern_catalog.py','wiki/articles/unreleased.json','wiki/articles/recent-changes.json','docs/adventure-journal/release-20261107/wiki-impact.json','docs/adventure-journal/release-20261107/wiki-publication.json']}
    for topic,files in paths.items():
        for path in files:
            row=dict(root=route,path=path,role='Reviewed Last Lantern paired live-QA release; normal-player acceptance remains open',revision=rev+' plus verified release evidence',sha256=hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
            existing=next((r for r in sources['topics'][topic] if r['root']==route and r['path']==path),None)
            if existing:existing.update(row)
            else:sources['topics'][topic].append(row)
    sources['observed_revisions']['last_lantern_live_qa_20261107']=rev
    sources['topics']['adventure-journal']=[r for t in ('world','items','client','operations','balance','wiki') for r in sources['topics'][t] if r['root']==route and r['path'] in paths[t]]
    after['references/sources.json']=json.dumps(sources,indent=2)+'\n'
    patch=''
    for name in names:
        patch+=''.join(difflib.unified_diff(before[name].splitlines(keepends=True),after[name].splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name))
    (OUT/'installed-skill.patch').write_text(patch,encoding='utf-8')
    if args.apply:
        for name in names:
            assert (SKILL/name).read_text(encoding='utf-8')==before[name],'Concurrent skill edit; re-review'
            (SKILL/name).write_bytes(after[name].encode('utf-8'))
    (OUT/'skill-maintenance.json').write_text(json.dumps({'applied':args.apply,'reviewed_revision':rev,'files':{n:hashlib.sha256(after[n].encode()).hexdigest() for n in names},'normal_player_accepted':False},indent=2)+'\n')
    print('Installed skill refreshed' if args.apply else 'Exact skill patch prepared; installation pending')

if __name__=='__main__':main()
