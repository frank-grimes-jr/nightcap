"""Prepare/apply reviewed dungeon knowledge with exact installed preimages.

This updates local knowledge only; it never installs gameplay or publishes wiki.
Run after source/evidence commits, then run the installed skill validators.
"""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
WORLD='''## Raid and Grind dungeon candidate

October 16 candidate: `docs/dungeons/README.md` and `QA.md` in the dungeon-modes
checkout own current evidence. Native `zone/dungeon_service.cpp` validates Keeper
operations and owns twelve-hour, six-participant, fixed-mode runs for all seven
dungeons. UUID + native allocation start + `nc-dungeon:<UUID>` identifies a run;
the 47-byte marker must fit native notes. Do not key progress on recyclable IDs.
Grind keeps native stats/timers. Raid has 135% HP/115% outgoing damage, permanent
spawn deaths and a final boss unlocked by all minibosses. Player-owned pets are
excluded from scaling. Explicit catalog revision 2026101601 has 52 objectives;
Permafrost excludes three audited later/nonqualifying native identities.

Encounter credit uses connected, loaded, enrolled party/owned-pet attribution
within a 200-unit 3D sphere. No retrospective credit; Grind respawns permit
catch-up. Tasks display the ledger; abandonment never resets eligibility.
Only the creator can confirm reset, with no pending/inside participants or
recoverable player corpses. Completed connections acknowledge entry/exit.
Earned claims and permanent completion counts survive reset and expiry.

Both-mode finalized corpse envelopes, Raid deaths, Grind timers and credit commit
before death publication. UUID checkpoints work independently of global state
saving; stale living checkpoints cannot override a newer death. Existing native
item/currency receipts filter replay. Uncertain persistence suspends the zone;
never clear receipts or restore older player data. Existing unmanaged runs retain
legacy behavior. SQL/content/cache drift and split game/content DB configuration
refuse activation/new runs/managed boot. Classic CT's pinned private 188-point,
29-NPC restoration does not change public spawn/door definitions.

Ship matching zone/world/shared_memory, regenerated target-content cache, SQL and
Keeper quest. The packaged cache is local-test content, not production content.
No client assets; a quest reload cannot install native hooks/cache. Automated
native policy/credit/spawn, receipt adapters, SQL/fault/concurrency and build/cache
evidence are separate from deployment. Fourteen-mode gameplay, CT path/door QA,
level-50 Vox/Nagafen balance and owner acceptance remain open. Source flow ends
at test; main/production restart and wiki publication require separate release.

'''
ITEMS='''## Dungeon reward catalog candidate

October 16 candidate only; `docs/dungeons/{catalog.json,README.md,QA.md}` owns
definitions and acceptance. IDs 960000–960329 remain below the RoF2 link ceiling.
Twenty-four shared designs (8 armor, 8 weapons, 6 accessories, 2 bags) use bands
20/30/40/50 and Normal/Polished/Ascended qualities: 288 definitions. Each dungeon
also has exactly three exclusive Raid designs in two qualities: 42 definitions.
Explicit budgets/defaults and cache-field checks prevent hidden stat drift.
Weapon delay is stable; bags use 6/8/10 slots, up to 100% weight reduction.

Grind completion grants Normal. Raid personal/exclusive qualities are 90%
Polished/10% Ascended; exclusive corpse count is 1/2/3 at 80/18/2%, without design
duplicates. Shared designs are uniform without class filtering. Run seed,
per-character reward ID and physical-drop UUID are durable; reconnect cannot
reroll. Completion grants once per character/run through the existing atomic
inventory/receipt transfer. Full inventories leave Keeper claims after expiry/reset.
All definitions are permanent, tradeable, non-attunable, non-lore and zero resale.
Existing legacy/zoneforge conversions exclude this range; do not treat dungeon
qualities as offsets or hunt Ascension. Native loot remains additional.

Source: `common/dungeon_{policy,catalog,contract}.h`, `zone/dungeon_service.cpp`,
`common/shareddb.cpp`, `tools/dungeon_{catalog,migration,contract}.py` and guarded
20261016 dungeon SQL. Tests: `tools/tests/test_dungeon*.py`, rehearsal/activation/
concurrency scripts, existing inventory/corpse adapter evidence and native cache
verification. Pair all native binaries with the cache; no client asset changes.
Local automated verification is not gameplay/balance acceptance or deployment.

'''

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    parser.add_argument('--deployed',action='store_true');args=parser.parse_args()
    world_section,items_section=WORLD,ITEMS
    if args.deployed:
        evidence=json.loads((ROOT/'docs/dungeons/deployment/production-verification.json').read_text())
        assert evidence['status']=='healthy' and evidence['gateway_open'] and evidence['enabled_revision']==2026101601
        world_section=WORLD.replace('## Raid and Grind dungeon candidate','## Raid and Grind dungeons deployed for live QA').replace('October 16 candidate:','October 16 deployed release:')
        world_section=world_section.replace('Keeper quest. The packaged cache is local-test content, not production content.','Keeper quest. Production startup regenerated its own cache; the older local-test\npackage cache must not replace it. Production preserved all 309,410 existing\nitem records and added exactly 330. See `docs/dungeons/deployment/` for native\nhashes, cache pairing, recovery and the separately recorded preflight DB restart.')
        world_section=world_section.replace('at test; main/production restart and wiki publication require separate release.','through dev/test to owner-authorized main and production deployment. The gateway\nis open. Website publication remains separate; owner gameplay is not accepted.').replace('Source flow ends\n','Source flow ran\n')
        items_section=ITEMS.replace('## Dungeon reward catalog candidate','## Dungeon reward catalog deployed for live QA').replace('October 16 candidate only;','October 16 deployed;').replace('Local automated verification is not gameplay/balance acceptance or deployment.','The regenerated production cache preserves all 309,410 old records and adds\nexactly 330 items. Deployment and continuing runtime checks pass; gameplay and\nbalance acceptance remain open. `docs/dungeons/deployment/` pins the actual pair.')
    out=ROOT/'docs/dungeons/skill-update';out.mkdir(exist_ok=True)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    world=(SKILL/'references/world.md').read_text(encoding='utf-8')
    items=(SKILL/'references/items.md').read_text(encoding='utf-8')
    wiki=(SKILL/'references/wiki.md').read_text(encoding='utf-8')
    # Reruns replace this bounded section, not append another history entry.
    for title in ('## Raid and Grind dungeon candidate','## Raid and Grind dungeons deployed for live QA'):
        if title in world:
            start=world.index(title);end=world.find('\n## ',start+len(title));world=world[:start]+(world[end+1:] if end>=0 else '')
    marker='## Travel failure diagnosis and current QA';assert marker in world
    world=world.replace(marker,world_section+marker)
    old='| Personal dungeon instances | `quests/global/Instance_Keeper.pl` | Separate NPC from waypoint; version **0** inherits native spawns/doors; seven custom Keepers, 12-hour instances |'
    if old in world:world=world.replace(old,'| Personal dungeon instances | `zone/dungeon_service.cpp`, `quests/global/Instance_Keeper.pl`, `docs/dungeons/` | Raid/Grind is a test candidate; existing live legacy runs retain version-zero content and twelve-hour lifetime |')
    if args.deployed:world=world.replace('Raid/Grind is a test candidate; existing live legacy runs retain','Raid/Grind is deployed for live QA; existing legacy runs retain')
    for title in ('## Dungeon reward catalog candidate','## Dungeon reward catalog deployed for live QA'):
        if title in items:
            start=items.index(title);end=items.find('\n## ',start+len(title));items=items[:start]+(items[end+1:] if end>=0 else '')
    items=items.replace('Keep the two tier systems distinct;','Keep the independent reward systems distinct;')
    marker='## Commonlands Leather Padding stock';assert marker in items
    items=items.replace(marker,items_section+marker)
    ledger=json.loads((SKILL/'references/sources.json').read_text(encoding='utf-8'))
    routes={
      'world':['server-mods/quests/global/Instance_Keeper.pl','server-mods/code/zone/dungeon_service.cpp',
        'server-mods/code/zone/spawn2.cpp','server-mods/code/zone/zone_save_state.cpp',
        'server-mods/sql/20261016_dungeons.sql','tools/tests/test_dungeon_lifecycle.py',
        'docs/dungeons/README.md','docs/dungeons/QA.md','docs/dungeons/concurrency-verification.json'],
      'items':['server-mods/code/common/shareddb.cpp','server-mods/code/common/dungeon_policy.h',
        'server-mods/code/common/dungeon_contract.h','tools/dungeon_catalog.py',
        'docs/dungeons/catalog.json','docs/dungeons/cache-verification.json',
        'docs/dungeons/activation-verification.json','docs/dungeons/package-manifest.json']}
    if args.deployed:
        routes['world']+=['docs/dungeons/deployment/production-verification.json','docs/dungeons/deployment/README.md','docs/dungeons/deployment/rollout.py','docs/dungeons/deployment/test_rollout.py']
        routes['items']+=['docs/dungeons/deployment/rehearsal.json','docs/dungeons/deployment/release-manifest.json','docs/dungeons/deployment/production-package-verification.json','docs/dungeons/native-build-manifest.json','tools/tests/test_dungeon_contract.py']
        routes['operations']=['docs/dungeons/deployment/README.md','docs/dungeons/deployment/rollout.py','docs/dungeons/deployment/production-verification.json']
    for topic,paths in routes.items():
        entries=ledger['topics'][topic]
        for relative in paths:
            p=ROOT/relative;assert p.is_file(),relative
            entry=dict(root=str(ROOT).replace('\\','/'),path=relative,
                role=('Reviewed Raid/Grind production deployment; owner gameplay acceptance pending' if args.deployed else 'Reviewed Raid/Grind candidate; automated evidence, not deployment or owner acceptance'),
                revision=revision,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            if args.deployed and relative in ('docs/dungeons/package-manifest.json','docs/dungeons/cache-verification.json'):
                entry['role']='Archived local-content test evidence; production build/cache pairing is recorded separately under deployment/'
            matches=[i for i,e in enumerate(entries) if e['path']==relative]
            if matches:entries[matches[0]]=entry
            else:entries.append(entry)
    wiki_root=Path('C:/Users/verre/.codex/worktrees/nightcap-wiki/EQ_Local_Dev')
    wiki_receipt=json.loads((ROOT/'docs/dungeons/wiki-update/receipt.json').read_text())
    for relative,digest in wiki_receipt['files'].items():
        path='wiki/'+relative
        assert hashlib.sha256((wiki_root/path).read_bytes()).hexdigest()==digest
        entry=dict(root=str(wiki_root).replace('\\','/'),path=path,
            role=('Reviewed local dungeon live-QA guide; not published; source patch in docs/dungeons/wiki-update' if args.deployed else 'Reviewed local dungeon candidate guide; not published; source patch in docs/dungeons/wiki-update'),
            revision=revision,sha256=digest)
        entries=ledger['topics']['wiki'];matches=[i for i,e in enumerate(entries) if e['path']==path]
        if matches:entries[matches[0]]=entry
        else:entries.append(entry)
    note='''\nDungeon candidate source update October 16: the maintained local wiki now has a
Not released Raid & Grind guide, linked from Features, Travel, In development
and Recent changes. Full-site Python/link and Node search/equipment checks pass.
Live catalog stats and live website release remain unchanged; publication is
pending. Exact preimages, installed source receipt and whole-wiki assessment:
`docs/dungeons/wiki-update/` and `docs/dungeons/wiki-review.md` in dungeon-modes.
'''
    marker='## Tests, publication and recovery'
    assert marker in wiki
    if args.deployed:
        note='''\nDungeon deployment source update October 16: the maintained local wiki has a
Live testing Raid & Grind guide, linked from Features, Travel and Recent changes.
The unreleased candidate notice was removed. The existing generated equipment
catalog remains specific to hunt rewards; dungeon rewards have a separate guide.
Full-site Python/link and Node search/equipment checks pass. Website publication
is pending. Exact preimages, installed source receipt and whole-wiki assessment:
`docs/dungeons/wiki-update/` and `docs/dungeons/wiki-review.md` in dungeon-modes.
'''
    for prefix in ('Dungeon candidate source update October 16:','Dungeon deployment source update October 16:'):
        if prefix in wiki:
            start=wiki.index(prefix);end=wiki.index(marker,start);wiki=wiki[:start]+wiki[end:]
    wiki=wiki.replace(marker,note+'\n'+marker)
    updates={'references/world.md':world,'references/items.md':items,'references/wiki.md':wiki,
             'references/sources.json':json.dumps(ledger,ensure_ascii=False,indent=2)+'\n'}
    if args.deployed:
        operations=(SKILL/'references/operations.md').read_text(encoding='utf-8')
        title='## Dungeon deployment resource and recovery contract'
        if title in operations:
            start=operations.index(title);end=operations.find('\n## ',start+len(title));operations=operations[:start]+(operations[end+1:] if end>=0 else '')
        operations+='''\n## Dungeon deployment resource and recovery contract

October 16 Raid/Grind release is on main and deployed for owner live QA; use
`docs/dungeons/deployment/` in the dungeon-modes checkout for current evidence.
The operator takes deployment/GM locks, retains a stopped full backup, rehearses
additive SQL and old/new loaders against public-only content, then regenerates
the actual production cache. It preserves 309,410 old items and adds 330.
Retain UUID ledgers/corpses/receipts; no old player snapshot restore or automatic
older-binary rollback. Uncertain SQL or opening acknowledgment closes access.

The initial buffered raw-row fingerprint exhausted the DB container's 2 GiB
limit at 18:53:02 UTC; MariaDB recovered at 18:53:04. Game/gateway did not restart
and no feature migration had begun. Use `--quick`, compact per-row SQL SHA-256
digests, DOUBLE-promoted FLOAT fields and a 128 MiB per-session memory cap.
Never buffer a full wide production item dump in a database-container client.
The active config is a read-only bind from `private/eqemu_config.json`; the
data/server path is an empty placeholder. Inspect mounts, keep secrets in memory
and redact credential-bearing SQL failures. MariaDB's utf8_general_ci and
utf8mb3_general_ci names are the sole audited schema-collation alias; do not
accept utf8mb4 or other metadata changes. Eleven focused and twenty operator
tests pass. In-game acceptance is separate; no new client assets are required.

The old world later stopped answering port 9001 without an image/container or
restart change. Ordinary preflight correctly failed, despite successful content
and cache rehearsal. A separately reviewed exact-identity completion recorded
the unhealthy baseline and revalidated public schema/content/config/native
processes before controlled activation. No cause was established for the old
stall. Check the native health port directly across >=15 seconds; cached Docker
health can lag. A zero container exit does not prove native flush: the supervisor
can kill remaining children after 75 seconds. Retain the shutdown receipt and
fresh stopped backup; never recover by replaying stale player snapshots.
'''
        updates['references/operations.md']=operations
    preimages={};patch=[]
    for relative,new in updates.items():
        target=SKILL/relative;old=target.read_bytes();preimages[relative]=hashlib.sha256(old).hexdigest()
        p=out/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(new,encoding='utf-8')
        patch.extend(difflib.unified_diff(old.decode('utf-8').splitlines(True),new.splitlines(True),fromfile='a/'+relative,tofile='b/'+relative))
    (out/'preimages.json').write_text(json.dumps(preimages,indent=2)+'\n')
    (out/'knowledge.patch').write_text(''.join(patch),encoding='utf-8')
    if args.apply:
        for relative in updates:
            assert hashlib.sha256((SKILL/relative).read_bytes()).hexdigest()==preimages[relative],relative
        for relative in updates:(SKILL/relative).write_bytes((out/relative).read_bytes())
        (out/'receipt.json').write_text(json.dumps(dict(status='installed',revision=revision,
            files={relative:hashlib.sha256((SKILL/relative).read_bytes()).hexdigest() for relative in updates}),indent=2)+'\n')
    print('Installed reviewed knowledge.' if args.apply else 'Exact knowledge update staged.')

if __name__=='__main__':main()
