"""Maintain reviewed Nightcap knowledge for the verified deployed release."""
import difflib,gzip,hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
WIKI=Path('C:/Users/verre/.codex/worktrees/aa-level-wiki/EQ_Local_Dev')

def main():
 assert json.loads((HERE/'deployed.json').read_text())['gateway_open']
 assert json.loads((HERE/'wiki-public-verification.json').read_text())['result']=='PASS'
 before={n:(SKILL/'references'/n).read_text(encoding='utf-8') for n in ('operations.md','world.md','items.md','balance.md','wiki.md','sources.json')}
 after=dict(before)
 def section(name,text):
  after[name]=re.sub(r'\n## .*?(?=\n## )','\n'+text+'\n',after[name],count=1,flags=re.S)
 section('operations.md','''## Chapterhouse — October23 deployed for live testing

Owner-authorized main PR311/c0c9896e and image db570029 are verified. Source:
C:/Users/verre/.codex/worktrees/camil-chapterhouse/EQ_Local_Dev. Paired
world97403fda/zone2c9323e4/shared_memory375814fe,13quests,both Vigil tables,
curated content and cache are installed. All12workers,45schema/532content checks
and427cache definitions pass;309844old cached items remain exact and13are added.
Classic50 and signed client2026102301 remain. No client patch is required.
Read docs/quests/camil-chapterhouse/deployment/README.md and deployed.json.
Owner native gameplay/balance acceptance remains open.

Fresh stopped backup and exact saved-state checks are retained. Initial activation
held after content because the shared preservation list includes the public
nightcap_waypoints catalog. Only its rehearsed addition differed; the tested
resume-v2 continuation reconciles that exact preflight checksum, preserving every
other saved table. Gateway143 is its observed normal Docker SIGTERM; native game
must exit0. Original held receipts remain in evidence/, successful continuation
in resume-evidence/. Never replay either operator or restore player snapshots.
Use compatible forward repair/pause while retaining earned claims and receipts.

Seventeen exact unmounted historical staging binaries were losslessly compressed
with decompressed SHA verification to recover3.5GiB. Adjacent recovery.gz copies
retain every byte; old operators require restoring their pinned staging copy.
No active image, runtime file or DB backup was removed. Source/native/arena/map
checks remain distinct from client-visible acceptance. Production still restarts
the whole supervised runtime on a native child exit.''')
 after['world.md']=after['world.md'].replace('## Camil Chapterhouse helmet quest — October23 implemented candidate','## Camil Chapterhouse helmet quest — October23 live testing')
 after['world.md']=after['world.md'].replace('feature/camil-chapterhouse, main5d0a0d31 plus reviewed candidate. Not deployed,\nnot owner accepted. Former multi-zone/design-only guidance is superseded.',
 'feature/camil-chapterhouse, promoted through PR311 to mainc0c9896e and deployed\nwith the paired native/content/quest/cache release. Owner acceptance remains open.\nDated delivery, hold recovery and exact QA: deployment/README.md under the quest docs.')
 after['world.md']=after['world.md'].replace('points and paired full native build pass. Candidate wiki patch is tested and\nunpublished. Public acquisition availability remains unchanged until activation.',
 'points and paired full native build pass. The campaign is enabled and public\naccess is open. Wiki20261023-camil-chapterhouse-v1 verifies483files; full native\nencounter and owner gameplay acceptance remain open.')
 after['items.md']=after['items.md'].replace('## Chapterhouse rewards — October23 candidate, not released','## Chapterhouse rewards — October23 live testing').replace('The reviewed Chapterhouse candidate appends','The deployed Chapterhouse release appends').replace('world.md and the candidate SPEC.md/RUNBOOK.md.\nNeither gameplay nor public item/zone catalog publication is authorized here.',
 'world.md, SPEC.md/RUNBOOK.md and deployment/deployed.json. The actual production\nloader preserved309844existing items and added13. Wiki483files includes the\n14item pages (new rewards plus unchanged helmet); owner gameplay QA is open.')
 after['balance.md']=after['balance.md'].replace('## Chapterhouse capstone — October23 candidate','## Chapterhouse capstone — October23 deployed for live testing').replace('The candidate keeps','The deployed encounter keeps').replace('This is an undeployed calibration,\nnot a live balance claim.',
 'The paired encounter is deployed for live testing, but these measurements are\nisolated native calibration, not accepted live encounter balance.')
 section('wiki.md','''## Chapterhouse guidance — October23 published

Current source is feature/chapterhouse-wiki in
C:/Users/verre/.codex/worktrees/aa-level-wiki/EQ_Local_Dev. Publication
20261023-camil-chapterhouse-v1 verifies483public files/476HTML and five private
denials. Twelve guides/home/Features/Recent changes describe the deployed Vigil
as Live testing. Native journal, maximum-legal-power difficulty, Ghoulbane/Slay,
warning counterplay, personal recovery and full-inventory claims are explained.
Owner visual, full encounter and balance acceptance remain open.

The catalog's separate chapterhouse projection and chapterhouse_catalog.py add
its zone and14item pages: four Ember qualities, three miniboss items, six final
Raid variants and the existing helmet. The original384Hunt variants/96families,
Build Lab, loot finder/timer and private guide remain. New equipment is not
incorrectly assigned the augment forging recipe. All24maintained guides and
447generated reward routes were reviewed; tests68Linux,15focusedWindows and
existing BuildLab/equipment Node suites pass. Exact verification/publication
receipts are in the gameplay checkout docs/quests/camil-chapterhouse/deployment/.
This dated release grants no standing publication or gameplay authority.''')
 manifest=json.loads(before['sources.json']);revision='c0c9896e151999e7002a453594079dae7b83bc41 + reviewed deployment evidence (2026-10-23; deployed, owner QA open)'
 reviewed=[]
 wiki_paths={'wiki/catalog.py','wiki/chapterhouse_catalog.py','wiki/catalog.json','wiki/README.md','wiki/test_wiki.py','wiki/content-review.json',
  *['wiki/articles/'+n+'.json' for n in ('camil-vigil','dungeon-modes','equipment','features','index','item-upgrades','recent-changes','travel','tunnel','unreleased','waypoints','zone-hunt')]}
 for topic,entries in manifest['topics'].items():
  for e in entries:
   root=Path(e['root'])
   if root==ROOT or (root==WIKI and e['path'] in wiki_paths):
    e['sha256']=hashlib.sha256((root/e['path']).read_bytes()).hexdigest();e['revision']=revision
    e['role']=e['role'].replace('candidate','live-testing release');reviewed.append([topic,e['path']])
 additions={'operations':['deployment/README.md','deployment/resume.py','deployment/test_rollout.py','deployment/deployed.json','deployment/preflight-receipt.json'],
  'world':['deployment/deployed.json'],'items':['deployment/deployed.json'],'wiki':['deployment/wiki-public-verification.json']}
 for topic,paths in additions.items():
  for name in paths:
   path='docs/quests/camil-chapterhouse/'+name
   if any(Path(e['root'])==ROOT and e['path']==path for e in manifest['topics'][topic]):continue
   manifest['topics'][topic].append({'root':ROOT.as_posix(),'path':path,'role':'reviewed Chapterhouse live-testing delivery/recovery evidence; owner QA open','revision':revision,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()});reviewed.append([topic,path])
 for path in ('wiki/catalog.py','wiki/chapterhouse_catalog.py','wiki/catalog.json','wiki/articles/camil-vigil.json'):
  if not any(Path(e['root'])==WIKI and e['path']==path for e in manifest['topics']['wiki']):
   manifest['topics']['wiki'].append({'root':WIKI.as_posix(),'path':path,'role':'published Chapterhouse guide/projection; existing Hunt values preserved','revision':revision,'sha256':hashlib.sha256((WIKI/path).read_bytes()).hexdigest()});reviewed.append(['wiki',path])
 manifest['observed_revisions']['chapterhouse_deployed_20261023']=revision
 after['sources.json']=json.dumps(manifest,indent=2,ensure_ascii=False)+'\n'
 patch=''.join(''.join(difflib.unified_diff(before[n].splitlines(True),after[n].splitlines(True),fromfile=n,tofile=n)) for n in before)
 (HERE/'skill-update.patch.gz').write_bytes(gzip.compress(patch.encode('utf-8'),mtime=0))
 for name,text in after.items():(SKILL/'references'/name).write_text(text,encoding='utf-8')
 (HERE/'knowledge-receipt.json').write_text(json.dumps({'reviewed':reviewed,'installed':True,'owner_gameplay_accepted':False},indent=2)+'\n')
 print(json.dumps({'installed_references':len(after),'reviewed_source_entries':len(reviewed)}))

if __name__=='__main__':main()
