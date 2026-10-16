"""Prepare exact installed-skill patch; install only with explicit --install.

The task requires maintaining these references. Installation compares preimages
so unrelated concurrent skill edits are never overwritten.
"""
import difflib
import hashlib
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
SOURCE=ROOT/'_worktrees/multiclass-trainer-access'
REV='114c730f246d771b5a480c515d9c1da94d3800c5'

BALANCE='''## Buried Sea AA audit — October 13, recommendation only

`E:/EQ_Local_Dev/docs/audits/aa-tbs-20261013/README.md` is the current AA catalog
review. Production content/rules were captured read-only at 09:33:44 UTC; all
6,655 rank rows require level 1, AA expansion gating is off, and 40% passive /
4,000 XP per point remain stored. No ranks are tagged expansion13, so TBS and TSS
cutoffs currently match. Conservative prerequisite-closed TBS pools retain
162–178 families / 2,861–3,413 points across six three-class profiles, versus
385–434 open families. These are class-mask catalog counts, not observed UI rows
or fresh fight results. Missing native prerequisites are not silently allowed.

Recommendation is TBS as outer bound, separate staged early-power caps and a
small utility/control list: Eyes Wide Open938 rank8, Diminutive Companion543
rank1, ENC Pet Discipline3202 rank1 with Animation Empathy195 rank3 prerequisite.
Pet HP3512/avoidance3818 through rank3 and Sturdy Companion1403 rank1 are
conditional trials; SPA397 contributes raw pet AC, not percentage mitigation.
TBS still retains deep defenses, Frenzied Devastation, Headshot/Anatomy, large
Tenacity HP, Mortal Coil and cheap glyphs. Later twincast/proc/resource engines
remain deferred. The historical solo combat cores included later pet support;
their victories do not validate a strict TBS pool on current production.

`families.csv`, `ranks.csv`, `class-coverage.csv` and `later-review.csv` enumerate
the offering. 1,310 later-rank families are inventoried, 45 individually reviewed
for content/source risks; remaining decisions are explicitly inventory triage.
`test_analysis.py` has eight focused closure/counting tests. Independent review
corrected spell-linked-versus-active labeling. All conclusions are proposals;
no runtime AA policy, fresh encounters or owner acceptance were added.

64 of 238 anonymous saved ownership rows contain later ranks. Preserve earned
ranks/charges/points and rerun per-character preflight before any enforcement.
Do not advance world CurrentExpansion just to gate AAs. Independent AA policy
needs matching server checks/cache refresh; new rule catalogs require world/zone
pairing, UI changes signed client delivery, and production native exits restart
the runtime. Exact level/build/encounter and ownership QA is in the report.
Reference-client title coverage is not signed-client verification. Current
captured custom2220/30196 point to Teleport42604/42603; the historical Ancient
Attunement99001/pet-spell finding does not describe this new content snapshot.

'''

MULTICLASS='''## AA catalog policy audit — October 13

Fresh read-only production data confirms every AA rank has level requirement1,
with expansion filtering off. See the [balance reference](balance.md) and
`E:/EQ_Local_Dev/docs/audits/aa-tbs-20261013/README.md` for the TBS rank-prefix
audit, complete inventory, later utility/pet exceptions and exact QA. This is a
recommendation, not an installed whitelist or solo-balance acceptance. Current
native AA send packets report expansion0; purchase level checks are distinct
from display eligibility. Do not use world CurrentExpansion13 as an AA-only cap.
64 saved rows include post-TBS ranks; preserve canonical earned ownership and
accounting through any later availability change. No cache/client pairing was
changed by the audit. Independent native enforcement/UI work remains future scope.

'''


def digest(b):
    return hashlib.sha256(b).hexdigest()


def prepare():
    targets={}
    for name,anchor,section in [('balance.md','## Source routes',BALANCE),
                                ('multiclass.md','## Skills and AA ownership',MULTICLASS)]:
        path=SKILL/'references'/name
        before=path.read_bytes()
        s=before.decode('utf-8')
        if section.splitlines()[0] in s:
            raise ValueError('Audit section already installed; inspect instead of appending')
        assert s.count(anchor)==1
        targets['references/'+name]=(before,s.replace(anchor,section+anchor).encode('utf-8'))
    path=SKILL/'references/sources.json'
    before=path.read_bytes();data=json.loads(before)
    data['observed_revisions']['aa_tbs_audit_source_20261013']=REV
    data['basis'] += ' AA TBS catalog audit refreshed October 13 from read-only production content and reviewed integrated AA/attack source; no new combat or deployment acceptance.'
    entries=[
        (ROOT,'docs/audits/aa-tbs-20261013/README.md','TBS audit findings, recommendations and exact unresolved gameplay QA'),
        (ROOT,'docs/audits/aa-tbs-20261013/summary.json','Fresh catalog/rule counts and anonymous purchase conflict classification'),
        (ROOT,'docs/audits/aa-tbs-20261013/production-snapshot.json.gz','Read-only production content/rules and anonymous ownership captured 2026-10-13'),
        (ROOT,'docs/audits/aa-tbs-20261013/analyze.py','Reviewed linked-rank prefixes, inherited prerequisite closure and class-union census'),
        (ROOT,'docs/audits/aa-tbs-20261013/review.py','Later-family inventory triage and 45 named content/source recommendations'),
        (ROOT,'docs/audits/aa-tbs-20261013/test_analysis.py','Eight policy-audit boundary and snapshot closure checks'),
        (SOURCE,'server-mods/code/zone/aa.cpp','Reviewed AA loading, inherited prerequisites, offer/purchase/use and expansion gates'),
        (SOURCE,'server-mods/code/zone/attack.cpp','Reviewed pet AC/avoidance and AC softcap inputs; not a fresh production binary probe'),
    ]
    for root,relative,role in entries:
        entry={'root':root.as_posix(),'path':relative,'role':role,
               'revision':REV if root==SOURCE else 'ce161c5 + reviewed AA audit working files (2026-10-13)',
               'sha256':digest((root/relative).read_bytes())}
        existing=data['topics']['balance']
        existing[:]=[e for e in existing if not(e['root'].replace('\\','/').rstrip('/')==root.as_posix() and e['path']==relative)]
        existing.append(entry)
    targets['references/sources.json']=(before,(json.dumps(data,indent=2)+'\n').encode())
    patch=[];manifest={}
    for relative,(before,after) in targets.items():
        candidate=HERE/'skill-update'/relative
        candidate.parent.mkdir(parents=True,exist_ok=True);candidate.write_bytes(after)
        manifest[relative]={'before_sha256':digest(before),'after_sha256':digest(after)}
        patch.extend(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),
                                         fromfile='a/'+relative,tofile='b/'+relative))
    (HERE/'nightcap-skill-update.patch').write_text(''.join(patch),encoding='utf-8')
    (HERE/'skill-update/preimages.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Prepared exact patch and guarded candidate files.')


def install():
    entries=json.loads((HERE/'skill-update/preimages.json').read_text())
    for relative,hashes in entries.items():
        assert digest((SKILL/relative).read_bytes())==hashes['before_sha256'],relative+' changed concurrently'
        assert digest((HERE/'skill-update'/relative).read_bytes())==hashes['after_sha256']
    for relative in entries:
        (SKILL/relative).write_bytes((HERE/'skill-update'/relative).read_bytes())
    receipt={'status':'installed','files':{r:digest((SKILL/r).read_bytes()) for r in entries}}
    (HERE/'skill-update/receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    install() if '--install' in sys.argv else prepare()
