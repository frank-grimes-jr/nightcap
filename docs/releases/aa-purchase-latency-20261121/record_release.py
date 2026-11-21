"""Record verified deployment/publication and prepare a guarded knowledge update."""
from pathlib import Path
import difflib
import hashlib
import json
import re
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ART=Path('E:/EQ_Local_Dev/artifacts/aa-purchase-latency-20261121')
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_bytes())
def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')


def main():
    deployed=read(HERE/'production-verified.json')
    public=read(HERE/'wiki-public-verification.json')
    published=read(HERE/'wiki-publication.json')
    build=read(HERE/'build.json')
    assert deployed['gateway_open'] and deployed['workers']==12 and not any(deployed['errors'].values())
    assert deployed['binaries']==build['binaries'] and public['result']=='PASS' and public['files']==631
    assert published['result']=='PASS' and published['services_preserved'] and published['channel_preserved']
    source=deployed['source']
    description=(f'Main PR515/{source[:8]} is deployed on all12zone workers with access open. '
        'Each purchase avoids the100-slot reset sweep; active deadlines, ownership and costs remain unchanged. '
        'Exact shipping reproduction/full native build,21cooldown tests,49native-client checks,5adjacent tests '
        'and10Windows/Linux rollout fault tests pass. Fresh stopped backup, saved-state/market, runtime-file, '
        'cache/client/service checks pass. Official wiki20261121-aa-purchase-latency-v1 verifies all631files. '
        'Owner visible-freeze acceptance remains OPEN. No client download; reconnect after maintenance.')
    path=ROOT/'CHANGES.md';text=path.read_text(encoding='utf-8')
    text,count=re.subn(r'## 2026-11-21 · AA purchase freeze candidate\n.*?(?=\n## )',
        '## 2026-11-21 · AA purchase responsiveness deployed\n\n- '+description+
        ' Evidence and QA: docs/releases/aa-purchase-latency-20261121/.\n',text,count=1,flags=re.S)
    assert count==1;path.write_text(text,encoding='utf-8',newline='\n')
    path=ROOT/'docs/status.md';text=path.read_text(encoding='utf-8')
    text,count=re.subn(r'## November 21, 2026 · AA purchase freeze candidate\n.*?(?=\n## )',
        '## November 21, 2026 · AA purchase responsiveness deployed\n\n'+description+
        ' [Evidence and exact QA](releases/aa-purchase-latency-20261121/README.md).\n',text,count=1,flags=re.S)
    assert count==1;path.write_text(text,encoding='utf-8',newline='\n')
    path=HERE/'README.md';text=path.read_text(encoding='utf-8')
    text=text.replace('Candidate built and tested; activation evidence will record installation.',
        f'Deployed from main PR515/{source} and verified on all12workers.\nOfficial wiki20261121-aa-purchase-latency-v1 is published and all631files verify.')
    text=text.replace('The candidate is not installed. Build artifacts are retained in the local Docker',
        'The candidate is installed. Exact production/runtime receipt: production-verified.json.\nBuild artifacts remain in the local Docker')
    text=text.replace('Public wiki publication remains pending.','Public wiki publication is verified; see wiki-publication.json and wiki-public-verification.json.')
    path.write_text(text,encoding='utf-8',newline='\n')
    validation=read(HERE/'validation.json');validation.update(deployment='PASS',main=source,workers=12,
        rollout_fault_tests={'Windows':10,'Linux':10},wiki_publication='PASS',public_files=631,player_acceptance='OPEN')
    save(HERE/'validation.json',validation)
    impact=read(HERE/'wiki-impact.json');impact.update(source=source,publication='VERIFIED20261121-aa-purchase-latency-v1',
        public_changed=['recent-changes.html','search-index.json'],public_preserved=629,
        authored_pages={p.stem:{'title':read(p)['title'],'sha256':sha(p)} for p in sorted((ROOT/'wiki/articles').glob('*.json'))})
    save(HERE/'wiki-impact.json',impact)
    candidate=read(HERE/'wiki-candidate-release.json');candidate['published']=True;save(HERE/'wiki-candidate-release.json',candidate)
    original={name:(SKILL/'references'/name).read_text(encoding='utf-8') for name in ('multiclass.md','operations.md','wiki.md','sources.json')}
    updated=dict(original)
    section=f'''## AA purchase responsiveness — November21 deployed for live testing

Main PR515/{source[:8]}, zone{build['binaries']['zone']},
image{deployed['image']}. Each committed purchase previously sent100timer resets,
each invoking pinned RoF2 receiver0x0b5bd0 → window update0x209f90. Purchases now
pass the purchased family: idle passive0timer packets; activated1ready reset;
running clocks retain stored deadlines under current rank/haste. Expired bought
families explicitly reset; Imitate Death legacy waits retire, Quick Buff stays
ready. No-argument login/class-change/bulk resets keep the full sweep.

Ownership transactions, prices, ranks, effects and authoritative durations stay.
Source/tests: E:/EQ_Local_Dev/_worktrees/aa-purchase-latency, zone/{{aa.cpp,client.h}},
tools/tests/test_aa_cooldown_identity.py (21tests) and eq-client-dll/tests/aa-reuse-native.cpp
(49pinned checks).5adjacent tests and10Windows/Linux rollout faults pass; shipping
predecessor13ad2534 reproduces exactly before freshPCH/fullAA compilation/link.
Nonvirtual overload only: Client layout/vtable/old symbol preserved.

Supported whole-runtime activation verified12workers, clean timed stop, fresh
stopped backup, saved-state/market, quests/plugins, cache/client/services and open
gateway. No SQL/rule/cache/client-download delta. Reconnect after maintenance.
Wiki20261121-aa-purchase-latency-v1 verifies631files,629unchanged. Owner freeze,
purchase/relog and cooldown acceptance remain OPEN. Exact receipts and Arena/
Chronicler QA: docs/releases/aa-purchase-latency-20261121/. Never kill one zone,
replay terminal operators or restore player snapshots. Uncertain drain/opening
closes admissions only; stop runtime automatically only after completed drain
and before any opening attempt. Preserve opening.json and receipt boundaries.

'''
    updated['multiclass.md'],count=re.subn(r'## AA purchase freeze — November21 candidate, not deployed\n.*?(?=## AA availability)',section,original['multiclass.md'],count=1,flags=re.S)
    assert count==1
    operations=f'''## Current production baseline · AA purchase responsiveness November21

Stage aa-purchase-latency-20261121-v1, main{source}, image{deployed['image']},
zone{build['binaries']['zone']}. Predecessor13ad2534 reproduced; fullAA TU built,
nonvirtual header overload only. World, content, rules, item/spell caches and signed
client2026112001 preserved. Fresh stopped backup, timed clean stop, saved-state/
market and runtime files verify; all12workers healthy, gateway open. Evidence:
E:/EQ_Local_Dev/_worktrees/aa-purchase-latency/docs/releases/aa-purchase-latency-20261121/.
Owner visible acceptance OPEN. Reconnect; no download. Never replay activation
or restore player data; uncertain admission opening requires occupancy review.

'''
    updated['operations.md']=original['operations.md'].replace('## Current production baseline · Classic defense November21',operations+'## Previous production baseline · Classic defense November21',1)
    wiki='''## AA purchase responsiveness · November21 published

Release20261121-aa-purchase-latency-v1 follows exactly reproduced Classic defense.
Only Recent changes and search change;631canonical HTTPS files and private404s
verify,629unchanged. All44authored guides plus Home/Features/commands and generated
catalogs reviewed; no mechanics/guide-step/numeric changes. Current repo guide
mirror lags public source: apply the scoped note to each independently to avoid
introducing unrelated missing anchors. Historical global ledger drift remains
REVIEW REQUIRED. Rollback rehearsal and game/client/service/config preservation
verify. Source/evidence: aa-purchase-latency worktree release directory. Owner
visible freeze and gameplay acceptance remain OPEN.

'''
    updated['wiki.md']=original['wiki.md'].replace('## Classic focus and defense',wiki+'## Classic focus and defense',1)
    sources=json.loads(original['sources.json'])
    paths=('server-mods/code/zone/aa.cpp','server-mods/code/zone/client.h','tools/tests/test_aa_cooldown_identity.py',
        'eq-client-dll/tests/aa-reuse-native.cpp',*[f'docs/releases/aa-purchase-latency-20261121/{n}' for n in
        ('README.md','build.json','validation.json','release.py','test_release.py','production-verified.json',
         'wiki-impact.json','wiki-publication.json','wiki-public-verification.json')])
    for topic in ('multiclass','operations','wiki'):
        for path in paths:
            if topic!='multiclass' and not path.endswith(('README.md','release.py','production-verified.json','wiki-impact.json','wiki-publication.json','wiki-public-verification.json')):continue
            rows=sources['topics'][topic];rows[:]=[x for x in rows if x['path']!=path]
            rows.append(dict(root=ROOT.as_posix(),path=path,role='Reviewed AA purchase deployed evidence; owner visible QA OPEN',
                revision='Main '+source+' + verified deployment records',sha256=sha(ROOT/path)))
    sources['observed_revisions']['aa_purchase_latency_deployed_20261121']=source
    sources['observed_revisions'].pop('aa_purchase_latency_candidate_20261121',None)
    updated['sources.json']=json.dumps(sources,indent=2,ensure_ascii=False)+'\n'
    pins={};patch=''
    for name,content in updated.items():
        target=SKILL/'references'/name;prepared=ART/('deployed-'+name)
        prepared.write_text(content,encoding='utf-8',newline='\n')
        pins[str(target)]={'before':sha(target),'after':sha(prepared),'prepared':str(prepared)}
        patch+=''.join(difflib.unified_diff(original[name].splitlines(True),content.splitlines(True),fromfile=str(target),tofile=str(target)))
    (HERE/'deployed-skill.patch').write_text(patch,encoding='utf-8',newline='\n')
    save(HERE/'deployed-skill-pins.json',pins)


if __name__=='__main__':main()
