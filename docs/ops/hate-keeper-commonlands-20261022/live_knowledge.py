"""Replace candidate knowledge with verified live evidence and current pins."""
import difflib,hashlib,importlib.util,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
WIKI=Path('E:/EQ_Local_Dev/_worktrees/hate-keeper-wiki')
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rev(p):return subprocess.check_output(['git','rev-parse','HEAD'],cwd=p,text=True).strip()
def main():
    d=json.loads((HERE/'deployment.json').read_text());p=json.loads((HERE/'wiki-public-verification.json').read_text())
    assert d['gateway_open'] and d['contract']=={'schema':39,'content':499} and p['result']=='PASS'
    out=HERE/'knowledge/live';out.mkdir(parents=True,exist_ok=False)
    names=['references/'+n for n in ('world.md','wiki.md','operations.md','sources.json')]
    before={n:(SKILL/n).read_text(encoding='utf-8') for n in names};pins={n:sha(SKILL/n) for n in names};after=dict(before)
    old=before['references/world.md'];start=old.index('## Hate Keeper in Commonlands');end=old.index('\n## ',start+4)
    section=old[start:end].replace('October22 candidate','October22 deployed for live QA').replace('Built/tested, not main-promoted or deployed; owner main/live sign-off is pending.',
      'Owner explicitly approved main/server promotion. PR299/a736fb0 and paired\nproduction activation are verified; owner native gameplay acceptance stays open.')
    section=section.replace('Install scoped SQL and the new zone together, with a full controlled runtime\nrestart. The read-only audit found zero unmanaged Hate instances; repeat the\nNULL-safe notes check after writers stop. Capture fresh public saved rows then;\ninvalidate only the old non-corpse Keeper, never restore player/run snapshots.',
      'Scoped SQL and zone1d4ef362 are live after a full controlled runtime restart.\nThe stopped NULL-safe check found zero unmanaged Hate instances. Fresh saved\nrows were captured, backed up and only the old public non-corpse Keeper scope\ninvalidated. Player/run state, quests, caches and other content were preserved.\nAll12 workers, native health and39/499 runtime checks verify; gateway is open.\nNever restore player/run snapshots or replay the isolated inverse after activity.')
    section=section.replace('Independent source/operator review completed; live execution and native QA remain\nopen. Evidence/recovery/exact QA:',
      'Independent source/operator review and live execution completed. Native owner\nvisibility/travel/gameplay QA remains open. Evidence/recovery/exact QA:')
    after['references/world.md']=old[:start]+section+old[end:]
    old=before['references/wiki.md'];start=old.index('## Hate Keeper relocation');end=old.index('\n## ',start+4)
    section='''## Hate Keeper relocation — October22 published for live testing

Current wiki release20261022-hate-keeper-v1 follows Build Lab. Source is
E:/EQ_Local_Dev/_worktrees/hate-keeper-wiki. Seven guides plus search now give
East Commonlands /loc -1570,-346,3, retained private Hate entrance and level46
entry without GM status. Owner-authorized PR299 and live activation are verified;
native visibility/travel/gameplay acceptance stays open. All22 guides/432 routes
reviewed; commands,384 Hunt item values, Build Lab and handbook preserved.

All466 HTTPS hashes/security headers and five private denials pass.16 local
content/source checks,16 Linux publisher/recovery tests and real pointer rollback
passed. No Nginx reload, private/config/service changes or client pairing.
The prior Build Lab payload was reproduced exactly before publication. Evidence:
docs/ops/hate-keeper-commonlands-20261022/ in the gameplay checkout. Source drift
records reconcile both branch histories; do not overwrite this newer publication.
'''
    after['references/wiki.md']=old[:start]+section+old[end:]
    after['references/wiki.md']=after['references/wiki.md'].replace('Current wiki release is `20261022-build-lab-v1` after the interactive handbook.','Build Lab was published as `20261022-build-lab-v1` after the interactive handbook;\nits payload is preserved by the subsequent Hate Keeper publication.')
    old=before['references/operations.md'];title,body=old.split('\n',1)
    after['references/operations.md']=title+'''\n\n## Hate Keeper Commonlands — October22 deployed

Owner-approved PR299/a736fb0 changes only zone executable1d4ef362 and scoped
Keeper content. All12 zones,39 schema/499 content checks, native health and open
gateway verify. Current world, shared_memory, quests, caches, client2204 and
unrelated services/content remain. Fresh stopped backup and player/custom/saved
state checks passed, with native expiry and one market rotation reconciled.
No database restoration. Private release stage:
/opt/nightcap/releases/hate-keeper-commonlands-20261022. Read redacted receipts
and recovery/owner QA in docs/ops/hate-keeper-commonlands-20261022/ from
E:/EQ_Local_Dev/_worktrees/hate-keeper-commonlands. Do not replay activation or
the isolated inverse. Public Hate now allows ordinary level46+ entry. Owner
in-game acceptance remains open. Wiki20261022-hate-keeper-v1 is verified.
\n'''+body.lstrip('\n')
    manifest=json.loads(before['references/sources.json'])
    for topic,root in (('world',ROOT),('wiki',WIKI)):
        for e in manifest['topics'][topic]:
            if e['root']==root.as_posix() and 'Hate Keeper candidate' in e['role']:
                e.update(revision=rev(root),sha256=sha(root/e['path']),role='Verified live Hate Keeper release; owner native gameplay acceptance open')
    extra=['docs/ops/hate-keeper-commonlands-20261022/'+n for n in ('deployment.json','README.md','authorization.json','wiki-publication.json','wiki-public-verification.json')]
    path='docs/ops/nightcap-wiki.md'
    manifest['topics']['wiki']=[e for e in manifest['topics']['wiki'] if e['path']!=path]
    manifest['topics']['wiki'].append(dict(root=WIKI.as_posix(),path=path,revision=rev(WIKI),sha256=sha(WIKI/path),role='Current published Hate Keeper wiki runbook; native QA open'))
    for topic in ('world','operations'):
        for path in extra:
            manifest['topics'][topic]=[e for e in manifest['topics'][topic] if e['path']!=path]
            manifest['topics'][topic].append(dict(root=ROOT.as_posix(),path=path,revision=rev(ROOT),sha256=sha(ROOT/path),role='Reviewed deployed Keeper/publication evidence; owner native QA open'))
    manifest['observed_revisions']['hate_keeper_deployed_20261022']=rev(ROOT)
    manifest['observed_revisions']['hate_keeper_wiki_published_20261022']=rev(WIKI)
    after['references/sources.json']=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
    patch=''.join(''.join(difflib.unified_diff(before[n].splitlines(True),after[n].splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in names)
    (out/'knowledge.patch').write_text(patch,encoding='utf-8')
    spec=importlib.util.spec_from_file_location('context',SKILL/'scripts/context.py');ctx=importlib.util.module_from_spec(spec);spec.loader.exec_module(ctx)
    for topic in ('world','wiki','operations'):
        result,drift=ctx.inspect(manifest,topic,check=True)
        (out/(topic+'-check.json')).write_text(json.dumps(result,indent=2)+'\n')
        assert not drift,topic
    assert all(sha(SKILL/n)==h for n,h in pins.items()),'Concurrent skill edit; regenerate'
    for n in names:(SKILL/n).write_text(after[n],encoding='utf-8',newline='\n')
    (out/'receipt.json').write_text(json.dumps({'preimages':pins,'afterimages':{n:sha(SKILL/n) for n in names},'result':'live evidence installed; zero drift'},indent=2)+'\n')
    print('Live world/wiki/operations knowledge installed with zero source drift.')
if __name__=='__main__':main()
