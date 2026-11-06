"""Maintain verified release records and prepare/apply only the reviewed installed knowledge delta."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development/references')
PUBLIC=ROOT/'artifacts/dungeon-readiness/wiki-source/wiki'


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def section(text,heading,replacement):
    start=text.index(heading);end=text.find('\n## ',start+len(heading))
    return text[:start]+replacement.rstrip()+'\n'+(text[end:] if end>=0 else '')


def main(apply):
    deployed=read(HERE/'deployed.json');wiki=read(HERE/'wiki-publication.json');https=read(HERE/'wiki-public-verification.json')
    assert deployed['gateway_open'] and deployed['status']=='deployed for live QA' and not deployed['owner_gameplay_accepted']
    assert deployed['checks']=={'schema':51,'content':671} and deployed['native_log_errors']==0
    assert wiki['result']==https['status']=='PASS' and wiki['files']==https['files']==510
    assert wiki['preserved_files']==507 and wiki['rollback_rehearsed']
    native=read(HERE.parent/'native-build-current.json')
    cache=read(HERE/'native-live-cache.json')
    assert cache['status']=='PASS' and cache['cache_definitions']==441 and cache['item_bytes']==1332
    zone=native['candidate_shipping_sha256'];image=deployed['runtime']['image_id'];source=deployed['source_revision']
    assert cache['runtime_image']==image and sum(name=='zone' and digest==zone for name,digest in deployed['runtime']['processes'])==12
    receipt=f'''## November6 — Instance Keeper Raid/Grind repair deployed for live QA

Owner-approved main PR415/{source[:8]} is deployed on OVH; player access is open.
Zone{zone[:16]} preserves the current automatic Stats/#augstats command archive,
signed client and world/shared_memory pair. All12zone hashes,51schema/671content
checks, all441actual live item-cache guards, unchanged content/rules/cache/commands
and104saved-state table boot model verify.
Fresh stopped backup integrity and one expected market rotation passed. No SQL,
cache regeneration, client update or player/run snapshot restore. Owner entry,
complete-run and balance acceptance remain open. Public wiki repair note/guide
verifies all510HTTPS files,507preserved, with rollback/private-route safeguards.
[Release, recovery and exact QA](dungeons/readiness-20261106/README.md).
'''
    path=ROOT/'docs/status.md';text=path.read_text(encoding='utf-8')
    heading=next(line for line in text.splitlines() if line.startswith('## November6 — Instance Keeper Raid/Grind repair'))
    text=section(text,heading,receipt)
    path.write_text(text,encoding='utf-8',newline='\n')
    path=ROOT/'CHANGES.md';text=path.read_text(encoding='utf-8')
    change=f'''## 2026-11-06 — Instance Keeper Raid/Grind repair deployed

Main PR415/{source[:8]} and the owner-authorized OVH zone-only release repair
both modes globally. Two compiled item batches/eight cache cases now accept the
already-released expedition augments; all other guards and current223-point Hate
layout remain. The native candidate reproduces automatic Stats baselineea6ad532
before its narrow relink. All12workers/51schema/671content checks, fresh stopped
backup, saved-state boot model and current content/cache/rules/command/client
preservation verify; access reopened. No migration, new client update or run reset.
Wiki510public HTTPS files/private denials and rollback pass. Owner gameplay QA
remains open. Evidence and exact QA: `docs/dungeons/readiness-20261106/`.
'''
    heading=next(line for line in text.splitlines() if line.startswith('## 2026-11-06 — Instance Keeper Raid/Grind'))
    text=section(text,heading,change)
    path.write_text(text,encoding='utf-8',newline='\n')
    path=HERE.parent/'README.md';text=path.read_text(encoding='utf-8')
    text=text.replace('# Instance Keeper readiness repair — November 6 authorized release','# Instance Keeper readiness repair — November 6 deployed for live QA',1)
    heading='\n## Verified production activation and publication\n'
    if heading not in text:
        text+=f'''{heading}
Main PR415/{source} is deployed as zone`{zone}` in image`{image}`.
All12workers/51schema/671content checks verify, fresh stopped backup integrity
passes, and saved-state/market boot effects match the recorded model. Content,
rules, all command settings, caches, quests, signed client and compatible native
consumers remain. Access is open. No new client update or SQL migration.

Wiki`{wiki['release']}` verifies510public HTTPS hashes/security headers and five
private denials;507files remain exact. Pointer rollback, private downloads,
Nginx and all five services are preserved. The exact published source is retained
under ignored`artifacts/dungeon-readiness/wiki-source`; source review and scoped
manifest are in`deployment/`. Historical global drift remains REVIEW REQUIRED.
Owner Crushbone Raid/Grind, entry/re-entry/Join, campaign/Hate and complete-run
gameplay/balance QA above remains open. Do not replay completed release jobs.
'''
    path.write_text(text,encoding='utf-8',newline='\n')
    # Reconcile only this fix into main's maintained prose; preserve other previews.
    live_note=read(PUBLIC/'articles/recent-changes.json')['body']
    live_note=live_note[:live_note.index('</p>')+4]
    for slug in ('recent-changes','unreleased'):
        path=ROOT/'wiki/articles'/(slug+'.json');data=read(path)
        if slug=='unreleased' and 'keeper-readiness-20261106' not in data['body']:continue
        assert 'keeper-readiness-20261106' in data['body']
        start=data['body'].index('<h2 id="keeper-readiness-20261106">');end=data['body'].index('</p>',start)+4
        data['body']=data['body'][:start]+(live_note if slug=='recent-changes' else '')+data['body'][end:]
        write(path,data)
    path=ROOT/'wiki/articles/dungeon-modes.json';data=read(path)
    sentence=' Use Enter to resume an existing run after an entry error; resetting is unnecessary.'
    if sentence not in data['body']:
        anchor='The creator chooses the mode.';assert data['body'].count(anchor)==1
        data['body']=data['body'].replace(anchor,anchor+sentence)
    write(path,data)
    impact=read(HERE.parent/'wiki-review.json')
    impact.update(status='published for live QA; gameplay acceptance open',public_release=wiki['release'],
                  publication_verification='deployment/wiki-public-verification.json;510files/507preserved',
                  current_source='Exact public-source reproduction and scoped guide/history edits in deployment/wiki-source-review.json')
    for row in impact['articles']:
        if row['slug'] in ('dungeon-modes','recent-changes'):row['decision']='published entry guidance / repair history'
        elif row['slug']=='unreleased':row['decision']='remove superseded local candidate note; no public candidate existed'
    write(HERE.parent/'wiki-review.json',impact)
    verification=read(HERE.parent/'verification.json')
    verification.update(status='deployed for live QA; owner gameplay acceptance open',candidate_shipping_sha256=zone,
        current_baseline_reproduced_sha256=native['retained_baseline_shipping_sha256'],
        linux_operator_tests=6,actual_live_cache_guards=441,saved_state_tables=deployed['saved_state_tables'],wiki_publication=wiki['release'],public_https_files=510,
        production_mutations='authorized supervised runtime restart and scoped wiki publication; no content/player migration',
        source_revision=source,open_gates=['Owner exact entry/gameplay/balance QA'])
    write(HERE.parent/'verification.json',verification)
    review=read(HERE.parent/'review.json')
    review.update(result='Verified deployed runtime and published wiki; owner gameplay acceptance remains open',
                  acceptance_open=['Owner exact entry/gameplay/balance QA'],
                  release_evidence='deployment/deployed.json; native-live-cache.json; wiki-public-verification.json')
    write(HERE.parent/'review.json',review)
    # Keep an exact source override for future publication from the actual checkout.
    patches=[];inputs=[]
    for path in sorted(PUBLIC.rglob('*')):
        rel=path.relative_to(PUBLIC)
        if not path.is_file() or rel.parts[0] in ('dist','__pycache__'):continue
        reference=ROOT/'wiki'/rel
        if path.suffix in ('.json','.py','.css','.js','.cjs','.html','.conf','.svg','.md','.txt'):
            before=reference.read_text(encoding='utf-8') if reference.exists() else ''
            after=path.read_text(encoding='utf-8')
            inputs.append(dict(path=rel.as_posix(),sha256=hashlib.sha256(after.encode()).hexdigest(),raw_sha256=sha(path),normalization='LF text'))
            patches.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/wiki/'+rel.as_posix(),tofile='b/wiki/'+rel.as_posix()))
        else:
            assert reference.is_file() and sha(reference)==sha(path),rel
            inputs.append(dict(path=rel.as_posix(),sha256=sha(path),raw_sha256=sha(path),normalization='exact binary bytes'))
    (HERE/'published-source-overrides.patch').write_text(''.join(patches),encoding='utf-8',newline='\n')
    write(HERE/'published-source-inputs.json',dict(inputs=inputs,files=510,scope='Public source only; main-only previews remain excluded'))
    names=('world.md','operations.md','wiki.md','sources.json')
    old={name:(SKILL/name).read_text(encoding='utf-8') for name in names};new={}
    world=f'''## Classic dungeons and compiled release readiness — November6 deployed for live QA

Managed catalog covers21Classic dungeons plus Chapterhouse/Kael expeditions;
revision2026101601 and all earned UUID/generation ownership remain.
Owner-approved main PR415/{source[:8]} and OVH activation are verified. Source:
{ROOT.as_posix()}; docs/dungeons/readiness-20261106/
and deployment/ own build, native/operator tests, backup/runtime/wiki receipts,
recovery and exact owner QA. Access open; native zone{zone[:16]}.
All12workers,51schema/671content checks, saved-state boot model and one expected
market rotation pass. Fresh stopped full backup verified; no player snapshot
restore. Owner entry/full-clear and solo/multiclass balance acceptance remain open.

The November6 content update left vigil/items/0 and compact/items/0 plus native
cache cases expecting eight older Chapterhouse/Kael augments. Both modes share
global fail-closed admission, so unrelated Crushbone requests failed too. Operator
overrides alone do not update compiled guards. dungeon_refresh_contract.py now
applies only reviewed release afterimage deltas, rejects compiler/SQL preimage
drift and retains historical setup SQL. Active Cinder Focus Type/Level/Level2
are checked. Never learn acceptance hashes from mutable production or rerun old
dungeon/augment setup. The generator is reproducible.

Retained live authority is671checks/223Hate points, not main's former650/176mirror.
The106reviewed Hate layout/density/landmark records are authenticated to retained
headerdfc7aadabc49f94c; all current positions, bosses and progress remain. Only
two SQL checks/eight native cases change;433other cache cases and all schemas/
669other content checks remain. Real ItemData/CacheMatches rejects eight released
afterimages before repair, accepts them after, and rejects33mutations.22dungeon,
10augment,20wiki and6Linux operator tests pass. A native checker against the
authenticated active game cache bind mount accepts all441definitions/1332byte
ItemData records without any player/run write.

Current relink reproduces deployed automatic Stats baselineea6ad532 byte-for-byte
from144authenticated link inputs, retains all12command archive members/protocol,
then replaces only the repaired dungeon object. Client's only new declaration
was nonvirtual RefreshEquippedStats; layout/vtable and other native objects stay.
Preserve automatic Stats/#augstats, signed0.13.4/2026110604, existing world/
shared_memory, metadata, content/cache/rules/quests and all earned UUID ledgers,
corpse envelopes, timers, journal credit and reward receipts. Zone-only repair:
no SQL/cache regeneration/client update or rule/quest reload. Never reset a run
to repair entry, restore players or kill an individual OVH zone child.

Activation uses current release guards plus zero-client checks, closed ingress,
125second native auth drain, supported whole-runtime stop, fresh stopped backup
and exact boot/market checks before reopening. Terminal one-shot jobs are not
replayable; failures hold access closed. Compatible held rollback retains current
data but reintroduces the known Keeper failure; after opening recover forward.
Wiki{wiki['release']} verifies all510HTTPS files/five private denials,507preserved.
Home/Features/commands/catalog mechanics remain; guide/history carry the repair.
Context topic dungeon-readiness pins reviewed source and verified deployment.
'''
    heading=next(line for line in old['world.md'].splitlines() if line.startswith('## Classic dungeons and compiled release readiness'))
    new['world.md']=section(old['world.md'],heading,world)
    start=old['operations.md'].index('Current signed');end=old['operations.md'].index('\n\n',start)
    client=old['operations.md'][start:end]
    client=client.replace('No runtime restart;\ncurrent native baseline is unchanged.','That XML-only publication required no runtime restart.')
    operations=f'''## Current native baseline — November6 Instance Keeper readiness repair

Owner-authorized main PR415/{source[:8]} is deployed for live QA; access open.
Source {ROOT.as_posix()}, docs/dungeons/readiness-20261106/deployment/.
Zone{zone};
image{image}. All12worker hashes,51schema/671content checks, fresh stopped full
backup, saved-state boot model, expected market rotation and unchanged content/
rules/cache/all-command-settings/quests/client verify. No player snapshot restore,
item/schema/rule/ItemData/Client-layout or world/shared_memory change. Preserve
worldf33c5925/shared_memory569394cf and current metadata consumers.

Retained local build /tmp/nightcap-dungeon-readiness-stats-20261106-v1 preserves
the repaired object from /tmp/nightcap-dungeon-readiness-20261106-v2. It first
reproduces automatic Stats zoneea6ad532 using its unchanged12member command
archive/protocol plus144authenticated inputs, then replaces only dungeon TU.
The older3fc-only orbc88-only Keeper candidates must not overwrite automatic
Stats. SQL/cache guards must follow released content; operator overrides cannot
change native admission. Exact tests/evidence/owner QA are in world.md.

{client}
No additional client update is needed for this Keeper repair. Gameplay acceptance
remains open. New release operators must preserve the full current pair and use
deployment/GM locks, zero native clients, closed-ingress125second auth drain,
supported whole-runtime stop, stopped backup and exact post-boot verification.
Never kill a production zone worker or replay terminal jobs. After opening use
fresh compatible forward repair; no old player/run snapshot restoration.
'''
    heading=next(line for line in old['operations.md'].splitlines() if line.startswith('## Current native baseline'))
    new['operations.md']=section(old['operations.md'],heading,operations)
    wiki_section=f'''## Instance Keeper readiness — November6 published for live QA

Wiki{wiki['release']} follows owner-authorized main PR415/OVH activation.
Exact previous510-file public source reproduced before only Dungeon modes,
Change Log and search change;507files remain exact. All510canonical HTTPS hashes/
security headers, five private-route denials (origin404/public403or404), pointer rollback, private downloads,
Nginx and five service identities/start times verify. No catalog/item/stat/drop/
command/unlock changes. Home/Features/summaries and all41authored/generated page
impacts reviewed; main-only previews remain excluded. Historical global source
drift remains REVIEW REQUIRED, not blanket-approved. Owner gameplay QA is open.
Source {ROOT.as_posix()}; docs/dungeons/readiness-20261106/deployment/
owns current public source inputs/overrides, publication and HTTPS evidence.
Do not republish an older full mirror or claim candidate text is live.
'''
    title='# Official player wiki and Features\n'
    heading='## Instance Keeper readiness — November6 published for live QA'
    new['wiki.md']=section(old['wiki.md'],heading,wiki_section) if heading in old['wiki.md'] else old['wiki.md'].replace(title,title+'\n'+wiki_section+'\n',1)
    manifest=json.loads(old['sources.json'])
    paths=['server-mods/code/common/dungeon_contract.h','tools/dungeon_contract.py','tools/dungeon_refresh_contract.py',
        'tools/tests/test_dungeon_release_readiness.py','tools/tests/test_dungeon_lifecycle.py','tools/build_dungeon_readiness.py',
        'tools/relink_dungeon_current.py','docs/dungeons/runtime-contract.json',
        'docs/dungeons/hate-boss-placement-20261030/runtime-checks.json','docs/audits/augments-20261106/item-preimages.json',
        'docs/dungeons/readiness-20261106/README.md','docs/dungeons/readiness-20261106/native-build-current.json',
        'docs/dungeons/readiness-20261106/production-target-contract.json','docs/dungeons/readiness-20261106/wiki-review.json']
    paths += ['docs/dungeons/readiness-20261106/deployment/'+name for name in
        ('rollout.py','test_rollout.py','linux-tests.json','deployed.json','AUTHORIZATION.md','wiki-publication.json','wiki-public-verification.json','wiki-source-review.json',
         'stage.py','run_action.py','verify_cache.py','native-live-cache.json','finalize.py',
         'reproduce_wiki.py','public-source-reproduction.json','published-source-inputs.json')]
    entries=[dict(root=ROOT.as_posix(),path=path,role='November6 reviewed Keeper repair deployed for live QA; owner gameplay acceptance open',
                  revision=source+' + verified release receipts',sha256=sha(ROOT/path)) for path in paths]
    verification['skill_update']=('applied' if apply else 'prepared; installation pending')+f'; {len(entries)} reviewed source fingerprints; deployment/maintenance.json'
    write(HERE.parent/'verification.json',verification)
    manifest['topics']['dungeon-readiness']=entries
    manifest['observed_revisions']['dungeon_readiness_deployed_20261106']=source+'; OVH/wiki verified; owner gameplay QA open'
    bypath={entry['path']:entry for entry in entries}
    for entry in manifest['topics']['world']:
        if entry['path'] in bypath:entry.update(bypath[entry['path']])
    new['sources.json']=json.dumps(manifest,indent=2)+'\n'
    patch=''.join(''.join(difflib.unified_diff(old[name].splitlines(True),new[name].splitlines(True),fromfile='a/references/'+name,tofile='b/references/'+name)) for name in names)
    (HERE/'installed-skill-deployed.patch').write_text(patch,encoding='utf-8',newline='\n')
    if apply:
        assert all((SKILL/name).read_text(encoding='utf-8')==old[name] for name in names),'Concurrent skill edit'
        for name,text in new.items():(SKILL/name).write_text(text,encoding='utf-8',newline='\n')
    write(HERE/'maintenance.json',dict(status='applied' if apply else 'prepared; installed patch pending',reviewed_source_entries=len(entries),
        current_native_zone=zone,source_revision=source,owner_gameplay_accepted=False,public_wiki=wiki['release']))
    print(json.dumps(dict(status='applied' if apply else 'prepared',fingerprints=len(entries),zone=zone,wiki=wiki['release'])))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    main(parser.parse_args().apply)
