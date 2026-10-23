"""Record the owner's scoped acceptance in installed Nightcap references."""
import difflib,hashlib,importlib.util,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
WIKI=Path('E:/EQ_Local_Dev/_worktrees/hate-keeper-wiki')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def revision(root):return subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
def main():
    acceptance=json.loads((HERE/'owner-acceptance.json').read_text(encoding='utf-8'))
    assert acceptance['message']=='Confirmed'
    names=['references/world.md','references/wiki.md','references/operations.md','references/sources.json']
    before={name:(SKILL/name).read_text(encoding='utf-8') for name in names}
    pins={name:sha(SKILL/name) for name in names};after=dict(before)
    world=before['references/world.md']
    world=world.replace('Owner explicitly approved main/server promotion. PR299/a736fb0 and paired\nproduction activation are verified; owner native gameplay acceptance stays open.',
      'Owner explicitly approved main/server promotion and replied "Confirmed" after\nactivation. PR299/a736fb0 and paired production activation are verified. The\nowner accepted relocation visibility and Hate travel; broader dungeon balance\nand full-clear QA remain separate.')
    world=world.replace('Independent source/operator review and live execution completed. Native owner\nvisibility/travel/gameplay QA remains open. Evidence/recovery/exact QA:',
      'Independent source/operator review and live execution completed. Owner\nconfirmed relocation visibility and Hate travel; broader dungeon balance and\nfull-clear QA remain separate. Evidence/recovery/exact QA:')
    after['references/world.md']=world
    wiki=before['references/wiki.md']
    wiki=wiki.replace('## Hate Keeper relocation — October22 published for live testing','## Hate Keeper relocation — October22 published and owner-confirmed')
    wiki=wiki.replace('native visibility/travel/gameplay acceptance stays open. All22 guides/432 routes',
      'the owner confirmed relocation visibility and Hate travel; broader dungeon\nbalance/full-clear QA remains separate. All22 guides/432 routes')
    after['references/wiki.md']=wiki
    operations=before['references/operations.md']
    operations=operations.replace('Public Hate now allows ordinary level46+ entry. Owner\nin-game acceptance remains open. Wiki20261022-hate-keeper-v1 is verified.',
      'Public Hate now allows ordinary level46+ entry. The owner replied "Confirmed"\nfor relocation visibility and Hate travel; broader dungeon balance/full-clear QA\nremains separate. Wiki20261022-hate-keeper-v1 is verified.')
    after['references/operations.md']=operations
    manifest=json.loads(before['references/sources.json'])
    for topic in ('world','wiki','operations'):
        for entry in manifest['topics'][topic]:
            if 'hate-keeper-commonlands-20261022' in entry['path']:
                entry['role']=entry['role'].replace('owner native QA open','owner relocation/visibility/travel acceptance confirmed; broader dungeon QA open')
                base=Path(entry['root']).resolve()
                entry['sha256']=sha(base/entry['path'])
                entry['revision']=revision(base)
        if topic in ('world','operations'):
            evidence = {
                'owner-acceptance.json': 'Owner-confirmed relocation/visibility/travel acceptance; broader dungeon QA remains separate',
                'wiki-before-confirmed.json': 'Guarded successor publication preimage; current release pointer and manifest',
                'wiki-publication-confirmed.json': 'Owner-confirmed wiki publication with rollback and private-service preservation',
                'wiki-public-verification-confirmed.json': 'Owner-confirmed public wiki hashes, security headers and private-route denials',
            }
            for name, role in evidence.items():
                path='docs/ops/hate-keeper-commonlands-20261022/'+name
                manifest['topics'][topic]=[e for e in manifest['topics'][topic] if e['path']!=path]
                manifest['topics'][topic].append({'root':ROOT.as_posix(),'path':path,'revision':revision(ROOT),'sha256':sha(ROOT/path),'role':role})
    wiki_paths = [
        'wiki/articles/dungeon-modes.json', 'wiki/articles/tunnel.json',
        'wiki/articles/travel.json', 'wiki/articles/features.json',
        'wiki/articles/index.json', 'wiki/articles/unreleased.json',
        'wiki/articles/recent-changes.json', 'wiki/content-review.json',
        'docs/ops/nightcap-wiki.md']
    wiki_root=WIKI.resolve(); wiki_revision=revision(wiki_root)
    manifest['topics']['wiki']=[e for e in manifest['topics']['wiki']
                                if e['root'] != wiki_root.as_posix()
                                or e['path'] not in wiki_paths]
    manifest['topics']['wiki'].extend(
        {'root':wiki_root.as_posix(),'path':path,'revision':wiki_revision,
         'sha256':sha(wiki_root/path),
         'role':'Owner-confirmed Hate Keeper relocation/visibility/travel wiki guidance; broader dungeon QA remains separate'}
        for path in wiki_paths)
    manifest['observed_revisions']['hate_keeper_owner_acceptance_20261022']=revision(ROOT)
    after['references/sources.json']=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
    out=HERE/'knowledge/acceptance';out.mkdir(parents=True,exist_ok=True)
    patch=''.join(''.join(difflib.unified_diff(before[name].splitlines(True),after[name].splitlines(True),fromfile='a/'+name,tofile='b/'+name)) for name in names)
    (out/'knowledge.patch').write_text(patch,encoding='utf-8')
    spec=importlib.util.spec_from_file_location('context',SKILL/'scripts/context.py');ctx=importlib.util.module_from_spec(spec);spec.loader.exec_module(ctx)
    checks={}
    for topic in ('world','wiki','operations'):
        report,drift=ctx.inspect(manifest,topic,check=True)
        # The installed ledger spans older checkouts and carries unrelated,
        # pre-existing drift. Prove the entries changed by this acceptance are
        # intact, while preserving the broader drift report for review.
        touched = {entry['path'] for entry in manifest['topics'][topic]
                   if ('hate-keeper-commonlands-20261022' in entry['path']
                       or entry['root'] == WIKI.resolve().as_posix())}
        acceptance_rows = [row for row in report['topics'][topic]
                           if Path(row['path']).as_posix().replace('\\','/').endswith(tuple(touched))]
        assert acceptance_rows and all(row.get('state') == 'unchanged' for row in acceptance_rows), (topic, touched, acceptance_rows)
        checks[topic]={'acceptance_entries': acceptance_rows,
                       'preexisting_or_unrelated_drift': [row for row in report['topics'][topic]
                                                          if row not in acceptance_rows],
                       'global_drift_present': drift}
        (out/(topic+'-check.json')).write_text(json.dumps(report,indent=2)+'\n')
    assert all(sha(SKILL/name)==digest for name,digest in pins.items()),'Concurrent skill edit; regenerate'
    for name in names:(SKILL/name).write_text(after[name],encoding='utf-8',newline='\n')
    (out/'receipt.json').write_text(json.dumps({'message':'Confirmed','scope':acceptance['scope'],'preimages':pins,'afterimages':{name:sha(SKILL/name) for name in names},'checks':checks,'note':'Acceptance entries verified unchanged; unrelated historical ledger drift is retained for separate review.'},indent=2)+'\n')
    print('Owner acceptance installed in Nightcap references; acceptance entries verified.')
if __name__=='__main__':main()
