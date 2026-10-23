"""Install reviewed candidate knowledge with preimage guards and a saved patch."""
import difflib,hashlib,importlib.util,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
WIKI=Path('E:/EQ_Local_Dev/_worktrees/hate-keeper-wiki')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def revision(root):return subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
def main():
    out=HERE/'knowledge';out.mkdir(exist_ok=True)
    names=('references/world.md','references/wiki.md','references/sources.json')
    before={name:(SKILL/name).read_text(encoding='utf-8') for name in names}
    pins={name:sha(SKILL/name) for name in names};after=dict(before)
    world='''## Hate Keeper in Commonlands — October22 candidate

Source E:/EQ_Local_Dev/_worktrees/hate-keeper-commonlands, feature/hate-keeper-commonlands.
Built/tested, not main-promoted or deployed; owner main/live sign-off is pending.
The public Hate Keeper998812/spawn9100012 moves to East Commonlands22 at
/loc -1570,-346,3 between Mirielle and Khalure. KeeperDungeon binds this exact
public host/NPC to Hate76. Admission precedes mutations; arrival uses destination
safe coordinates and JournalForRun selects Hate. A private-only spawn overrides
the moved base on fresh and checkpoint loads, retaining the entrance service.
Removing Hate's status80 restriction also opens public classic Hate to ordinary
level46+ players; level46 is retained. No client/quest/world/cache change.

Install scoped SQL and the new zone together, with a full controlled runtime
restart. The read-only audit found zero unmanaged Hate instances; repeat the
NULL-safe notes check after writers stop. Capture fresh public saved rows then;
invalidate only the old non-corpse Keeper, never restore player/run snapshots.
39schema/499content successor checks, exact-baseline build,18 source regressions,
SQL forward/failure/inverse/scope rehearsal and production-matching terrain pass.
Independent source/operator review completed; live execution and native QA remain
open. Evidence/recovery/exact QA: docs/ops/hate-keeper-commonlands-20261022/.

'''
    wiki='''## Hate Keeper relocation — October22 candidate guidance

E:/EQ_Local_Dev/_worktrees/hate-keeper-wiki branches from the published Build Lab
source5dff50c. Seven Not released notices cover Hate's proposed Commonlands spot,
level46 access and private entrance continuity. All22 guides/432 generated routes
were assessed; commands,384 Hunt catalog values, Build Lab and the interactive
handbook remain.16 wiki checks pass and459 pages build. Source drift is recorded
without blindly advancing the ledger. This candidate is not published and does
not supersede the current Build Lab public release. Main/live and owner QA gates
remain open. Evidence: docs/ops/hate-keeper-commonlands-20261022/wiki-review.json
in the gameplay candidate checkout; publish only after verified live activation.

'''
    for name,section in (('references/world.md',world),('references/wiki.md',wiki)):
        assert section.splitlines()[0] not in before[name]
        title,body=before[name].split('\n',1);after[name]=title+'\n\n'+section+body.lstrip('\n')
    manifest=json.loads(before['references/sources.json'])
    entries={
      'world':(ROOT,['server-mods/code/zone/dungeon_service.cpp','server-mods/code/common/dungeon_policy.h','server-mods/code/common/dungeon_catalog.h','server-mods/code/common/dungeon_contract.h','docs/dungeons/runtime-contract.json','tools/hate_keeper.py','tools/dungeon_catalog.py','tools/dungeon_refresh_contract.py','tools/tests/test_hate_keeper.py','tools/tests/test_hate_keeper_content.py','tools/tests/test_classic_dungeon_private.py','tools/tests/test_dungeon_journal.py','docs/ops/hate-keeper-commonlands-20261022/README.md','docs/ops/hate-keeper-commonlands-20261022/rollout.py']),
      'wiki':(WIKI,['wiki/articles/'+slug+'.json' for slug in ('dungeon-modes','tunnel','travel','features','index','unreleased','recent-changes')]+['wiki/content-review.json'])}
    for topic,(root,paths) in entries.items():
        rev=revision(root)
        manifest['topics'][topic]=[e for e in manifest['topics'][topic] if e['path'] not in paths]
        manifest['topics'][topic]+=[dict(root=root.as_posix(),path=path,revision=rev,sha256=sha(root/path),role='Reviewed Hate Keeper candidate; main/live, publication and owner QA pending') for path in paths]
        manifest['observed_revisions']['hate_keeper_'+topic+'_candidate_20261022']=rev
    after['references/sources.json']=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
    patch=''.join(''.join(difflib.unified_diff(before[n].splitlines(True),after[n].splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in names)
    (out/'knowledge.patch').write_text(patch,encoding='utf-8')
    spec=importlib.util.spec_from_file_location('skill_context',SKILL/'scripts/context.py');ctx=importlib.util.module_from_spec(spec);spec.loader.exec_module(ctx)
    baseline=json.loads(before['references/sources.json']);report={}
    for topic in entries:
        old,_=ctx.inspect(baseline,topic,check=True);new,drift=ctx.inspect(manifest,topic,check=True)
        old_bad={r['path'] for r in old['topics'][topic] if r['state']!='unchanged'}
        new_bad={r['path'] for r in new['topics'][topic] if r['state']!='unchanged'}
        assert new_bad<=old_bad,'Introduced knowledge drift'
        report[topic]={'introduced_drift':[],'preexisting_drift':sorted(new_bad)}
        (out/(topic+'-check.json')).write_text(json.dumps(new,indent=2)+'\n')
    assert all(sha(SKILL/n)==h for n,h in pins.items()),'Concurrent skill update; regenerate'
    for name in names:(SKILL/name).write_text(after[name],encoding='utf-8',newline='\n')
    receipt={'preimages':pins,'afterimages':{n:sha(SKILL/n) for n in names},'status':'candidate installed','checks':report}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'installed':True,'new_drift':0,'preexisting_drift':{t:len(v['preexisting_drift']) for t,v in report.items()}}))
if __name__=='__main__':main()
