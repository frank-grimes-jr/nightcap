"""Refresh only this release's installed skill section and reviewed fingerprints."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')

def replace_section(path, heading, text):
    source=path.read_text(encoding='utf-8')
    start=source.index('## '+heading)
    end=source.index('\n## ',start+3)
    path.write_text(source[:start]+text.rstrip()+'\n'+source[end:],encoding='utf-8')

def main():
    deployed=json.loads((HERE/'deployed.json').read_text())
    wiki=json.loads((HERE/'wiki-public-verification.json').read_text())
    assert deployed['status']=='activated_verified' and wiki['result']=='PASS'
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    replace_section(SKILL/'references/world.md','Global keyless doors', '''## Global keyless doors — October29 deployed for owner QA

Owner-authorized main PR370 (7cb0ec4a), acknowledgment repair PR371 (0e0970e3),
natural-unload continuation PR372 (17509a22), and guarded OVH activation removed all194 existing door locks across48zones,
including129 negative lockpick sentinels. All19272 rows match the exact expected
afterimage;19078 unrelated doors remain unchanged. Only doors.keyitem/lockpick
became0. Guild/trigger/adventure/quest/zone/instance eligibility remains. No item,
keyring, player, encounter or reward change. Future content imports require lock
review; this is a content migration, not a permanent native bypass.

Source: E:/CodexData/home/worktrees/keyless-doors/EQ_Local_Dev;
tools/keyless_doors.py and keyless_doors_capture.py. Four policy/three Hole tests,
nine real production-schema SQL rehearsal groups and14 operator/recovery tests
pass. FLOAT-to-DOUBLE companions reconstruct exact native storage while CAST-to-
CHAR rows match SQL guards. Raw capture/SQL/QA coordinates remain ignored under
docs/ops/keyless-doors-20261029/private/. Never publish these captures.

Full PEQ backup verified before writes. Paineel was the only affected loaded
zone; an owned native zone75 admission hold preceded a125second auth drain.
Paineel naturally unloaded during that drain without exiting its worker. The
second pre-SQL guard stopped on that state change; resume_unloaded.py verified
no affected loaded/booting zones and applied the original guarded transaction.
No static reload was needed; normal future loads read updated definitions. The first attempt stopped
before SQL on missing broadcast acknowledgment; exact unchanged DB/worker/lock
evidence allowed the one-use resume_activation.py continuation. Successful lock
broadcasts do not return to a status-only connection: use an ordered explicit
List readback, accepting numbered List rows only. Persist the lock preimage before
mutation and release only its exact owned postimage. No uncertain SQL retry.

All12 zone worker and five service lifetimes remained unchanged, full content
and health checks passed, and the original native lock list was restored.
No world restart/market rotation, binary/cache/client update. Other affected
zones use new rows on normal load. Static reload also touches traps, objects,
ground spawns and zonepoints; review each loaded target and never kill workers.
Rollback uses guarded two-column inverse against current exact afterimages,
never player/keyring snapshots. Operator sources/tests, deployed.json,
activation-guard.json, backup/recovery and exact non-GM QA are in
docs/ops/keyless-doors-20261029/. Owner gameplay acceptance remains pending.
''')
    replace_section(SKILL/'references/wiki.md','Global keyless doors', '''## Global keyless doors — October29 published for live testing

Wiki20261029-keyless-doors-v1 is live following verified194-door/48-zone OVH
activation (main PR370, operator corrections PR371/372). Travel, Features,
In development, Change Log and generated zone-hole guidance describe global
keyless doors while preserving other access restrictions and pending gameplay
acceptance. All40 authored surfaces and generated catalog sources reviewed;
Home/commands/reward values are unchanged. Historical October24 entries retain
their dated scope. Six files changed,493 baseline files preserved. All499 HTTPS
hashes/security headers and five private404 routes verify;19 content/refresh,
search and16 Linux publication/recovery tests pass. No raw captures are public.

Source: E:/CodexData/home/worktrees/keyless-doors/EQ_Local_Dev;
docs/ops/keyless-doors-20261029/ owns release review, strict package baseline,
activation guard, publication and HTTPS receipts. Historical unrelated source
drift remains REVIEW REQUIRED, with no blanket ledger advance. The release was
scoped from main; unrelated dev/test candidate pages were not published.
''')
    path=SKILL/'references/sources.json'
    data=json.loads(path.read_text(encoding='utf-8'))
    data['observed_revisions']['keyless_doors_deployed_20261029']=deployed['continuation_revision']
    data['observed_revisions']['keyless_doors_evidence_20261029']=revision
    paths={
      'world':['tools/keyless_doors.py','tools/keyless_doors_capture.py',
       'tools/tests/test_keyless_doors.py','tools/tests/rehearse_keyless_doors.py']+
       ['docs/ops/keyless-doors-20261029/'+p for p in ['README.md','production-plan.json',
        'production-rehearsal.json','activate.py','runtime.py','resume_activation.py',
        'resume_unloaded.py','test_activation.py','deployed.json','activation-guard.json']],
      'wiki':['wiki/articles/'+p+'.json' for p in ['travel','features','unreleased','recent-changes']]+
       ['wiki/catalog.py']+['docs/ops/keyless-doors-20261029/'+p for p in
        ['wiki-release-review.json','wiki-release-refresh.json','wiki-publication.json','wiki-public-verification.json']]}
    for topic,files in paths.items():
        data['topics'][topic]=[e for e in data['topics'][topic] if 'keyless-doors' not in e.get('root','')]
        for relative in files:
            data['topics'][topic].append(dict(root=str(ROOT).replace('\\','/'),path=relative,
              role='October29 deployed keyless doors and verified wiki; owner gameplay QA open',
              revision=revision,sha256=hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()))
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Updated world/wiki knowledge and',sum(map(len,paths.values())),'reviewed fingerprints')

if __name__=='__main__':main()
