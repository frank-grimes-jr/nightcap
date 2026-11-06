"""Reconcile actual verified release receipts; never infer owner acceptance."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PUBLIC=ROOT/'artifacts/character-stats/wiki-source/wiki'


def main():
    deployed=json.loads((HERE/'deployed.json').read_text())
    client=json.loads((HERE/'client-public-verification.json').read_text())
    wiki=json.loads((HERE/'wiki-publication.json').read_text())
    assert deployed['gateway_open'] and not deployed['database_restored'] and not deployed['cache_changed']
    assert client['release']==2026110602 and client['hosted'] and client['changed_assets']==3
    assert wiki['result']=='PASS' and wiki['files']==510
    for folder in (ROOT/'wiki',PUBLIC):
        for slug in ('augment-audit','equipment','commands','features','recent-changes'):
            p=folder/'articles'/(slug+'.json');o=json.loads(p.read_text(encoding='utf-8'))
            o['sources']=[v.replace('signed2026110602/native ea6ad532 candidate, owner QA open',
                        'signed2026110602/native ea6ad532 verified for live QA; owner acceptance open') for v in o['sources']]
            p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    diff=[];inputs=[]
    for path in sorted(PUBLIC.rglob('*')):
        rel=path.relative_to(PUBLIC)
        if not path.is_file() or not (rel.parts[0]=='articles' and path.suffix=='.json' or
            rel.as_posix() in ('build.py','catalog.py','catalog.json','chapterhouse_catalog.py','augment_candidate.py','augment-candidate.json')):continue
        inputs.append(rel);base=ROOT/'wiki'/rel
        before=base.read_text(encoding='utf-8') if base.exists() else '';after=path.read_text(encoding='utf-8')
        diff.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/wiki/'+rel.as_posix(),tofile='b/wiki/'+rel.as_posix()))
    patch=HERE/'published-source-overrides.patch';patch.write_text(''.join(diff),encoding='utf-8',newline='\n')
    rep=ROOT/'artifacts/character-stats/reproduced-final'
    rep.mkdir();shutil.copytree(ROOT/'wiki',rep/'wiki',ignore=shutil.ignore_patterns('dist','__pycache__'))
    shutil.copytree(ROOT/'config',rep/'config')
    for rel in inputs:
        p=rep/'wiki'/rel
        if p.exists():p.write_text(p.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
    subprocess.run(['git','apply','--directory=artifacts/character-stats/reproduced-final',str(patch)],cwd=ROOT,check=True)
    for rel in inputs:assert (rep/'wiki'/rel).read_text(encoding='utf-8')==(PUBLIC/rel).read_text(encoding='utf-8'),rel
    subprocess.run(['python',str(rep/'wiki/build.py')],check=True)
    hashes=lambda folder:{p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
    assert hashes(rep/'wiki/dist')==hashes(PUBLIC/'dist')
    (HERE/'public-source-reproduction.json').write_text(json.dumps(dict(status='PASS',source_inputs=len(inputs),files=510,
        method='main source/patch normalized to LF; overrides reproduce79 source inputs and510 public output files'),indent=2)+'\n')
    p=ROOT/'docs/status.md';text=p.read_text(encoding='utf-8');a=text.index('## November6 — automatic equipped Stats candidate');b=text.index('\n## ',a+5)
    text=text[:a]+'''## November6 — automatic equipped Stats deployed; owner QA open

Main PR410/313d497c is deployed on OVH with access reopened. Inventory Stats has
server-backed totals/caps, Shield Block, strongest Hunt contribution, relative
Dodge, item focus potential and worn Faerune. Refresh is silent and automatic.
#augstats remains a diagnostic fallback. No gameplay power, loot, player-data,
cache, rule or command-setting change. Native zone ea6ad532 retains compatible
world/shared_memory. Stopped backup, saved-state/content/native checks passed.

Signed2026110602/proxy0.13.4 is published:148hosted assets/signature/pair verified;
only DLL/catalog/Inventory XML changed,145other descriptors/URLs preserved.
Fully EXIT EQ/use launcher Play; relog alone cannot replace the loaded DLL.
Wiki20261106-character-stats-v1 passed510-file/rollback/private-download/service
checks. [Details and exact Palwar/The Hole QA](releases/character-stats-window-20261106/README.md).
Native pixels, scrolling, actual live refresh and owner gameplay acceptance remain
open. Automated native fixtures and delivery checks are separate from acceptance.
''' +text[b:];p.write_text(text,encoding='utf-8')
    p=ROOT/'CHANGES.md';text=p.read_text(encoding='utf-8');a=text.index('## 2026-11-06 — Server-backed character Stats candidate');b=text.index('\n## ',a+5)
    text=text[:a]+'''## 2026-11-06 — Server-backed character Stats deployed for live QA

Main PR410 adds automatic server-backed totals/caps to Inventory Stats, including
Shield Block/Hunt, relative Dodge, worn item focus potential and Faerune. Actual
damage/healing caps include earned headroom. Missing/stale data shows --. Existing
#augstats remains a fallback. No item power, stacking, loot, player data, rules,
cache, command settings or native Client ABI change. Quiet polls retain permission
checks and avoid command logs/quest callbacks. Supported whole-runtime update,
fresh stopped backup and saved-state/native/content checks passed; access is open.
Signed0.13.4/2026110602 changes3/148assets,145unchanged descriptors/URLs retained;
all HTTPS hashes/production signature/pair verify. Fully EXIT EQ/use launcher Play.
Wiki510files/rollback/private routes/services verified. Owner native sizing,
scrolling, refresh and gameplay acceptance remains open.
Evidence: `docs/releases/character-stats-window-20261106/`.
''' +text[b:];p.write_text(text,encoding='utf-8')
    p=HERE/'README.md';text=p.read_text(encoding='utf-8');text+=f'''
## Verified deployment and publication

Main PR410 merged as313d497c479db5b15c3d4fc622abb4625a8aa4ae. All one-shot
preflight/activate/open jobs returned0. `deployed.json` is fresh readback of zone
ea6ad532, compatible unchanged world/shared_memory, unchanged content/rules/cache
and all command settings. Runtime image {deployed['runtime']['image_id']}.
Saved-state boot/market rotation verified before reopening; no old player restore.
Stopped backup SHA256 {deployed['backup']['sha256']} passed gzip integrity.

Signed2026110602/proxy0.13.4 is published; `client-public-verification.json` checks
all148HTTPS assets/{client['verified_bytes']}bytes, production-key signature,
history/tombstones and DLL/catalog pairing. Three changed files,145preserved.
Full EQ exit/launcher Play required. Wiki20261106-character-stats-v1 verifies510
files/503HTML routes, private downloads, rollback and unchanged service identities/
starts. Source overrides reproduce79inputs and510outputs while preserving main's
unrelated unpublished previews. Global historical drift remains REVIEW REQUIRED.

Before reopening, held native rollback can select the compatible prior image;
after reopening use a fresh compatible forward repair. Never replay terminal jobs
or restore an old player snapshot. Signed client recovery requires a higher
counter and matched DLL/catalog/XML; old lower counters must not be republished.
Owner native pixels/skin/resize/scroll/refresh and gameplay acceptance remains
open. Delivery and synthetic native tests do not establish player acceptance.
''';p.write_text(text,encoding='utf-8')
    p=ROOT/'docs/README.md';text=p.read_text(encoding='utf-8');text=text.replace('# Nightcap documentation\n',
        '# Nightcap documentation\n\n- [Automatic character Stats: deployed update and exact native QA](releases/character-stats-window-20261106/README.md)\n',1);p.write_text(text,encoding='utf-8')
    p=HERE/'wiki-impact.json';o=json.loads(p.read_text());o['publication']='verified20261106-character-stats-v1;510files, rollback/private downloads/services pass';p.write_text(json.dumps(o,indent=2)+'\n')
    p=HERE/'review.json';o=json.loads(p.read_text());o['status']='deployed for live QA; owner native acceptance open';o['publication']='OVH native, signed2026110602/all148HTTPS assets and wiki510files verified';p.write_text(json.dumps(o,indent=2)+'\n')
    print('Reconciled verified release; owner native acceptance remains open.')


if __name__=='__main__':main()
