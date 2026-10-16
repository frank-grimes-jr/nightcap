"""Replace superseded AA level-gate guidance; preserve concurrent system knowledge."""
import difflib, hashlib, json, os, subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def section(text,start,end,replacement):
    a=text.index(start);b=text.index(end,a);return text[:a]+replacement.strip()+'\n\n'+text[b:]

def main():
    health=json.loads((HERE/'post-notes-health.json').read_text(encoding='utf-8'))
    hosted=json.loads((HERE/'hosted-notes-verification.json').read_text(encoding='utf-8-sig'))
    assert health['gateway_open'] and health['runtime']['restart_count']==0 and hosted['verified_files']==105
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    paths=['references/balance.md','references/multiclass.md','references/client.md','references/sources.json']
    before={n:(SKILL/n).read_bytes() for n in paths}
    texts={n:b.decode('utf-8').replace('\r\n','\n') for n,b in before.items()}
    balance=f'''## Buried Sea AA policy — level-1 correction deployed October 13

**Every allowed AA and rank is available at character level 1.** Players decide
where and when to spend points. The owner rejected the initial level-gated
starter list during live QA; never reintroduce character-level AA gates.
Balance with the release's legal pool, rank ceilings, costs and prerequisites.

Current evidence: `{ROOT.as_posix()}/docs/releases/aa-tbs-level1-20261013/README.md`.
OVH image `{health['runtime']['image_id']}` runs the correction on all12 zones.
All239 ownership rows/1193 earned ranks and47 player/11 custom tables survived.
Zero restarts/detected native, quest or DB errors in the recorded check. Manual
creation/purchase/reconnect/pet/combat QA and main promotion remain pending.

`era.json` selects `config/aa-policy.json`; rank counts replace level arrays.
The same390 families/941 ranks are legal at every level. Most ordinary families
have a three-rank release ceiling. Native offers, use, purchases and default
grants ignore original DB level_req for clients; unknown identities fail closed.
Explicit GM GrantAllAAPoints unlock_level remains an optional content filter,
not a player gate. Non-client purchase behavior remains native.

TBS13 is independent of the Classic world. The six later exceptions all open
at1: Eyes Wide Open938 eight ranks; Diminutive543 one; ENC Pet Discipline3202
one requiring Animation Empathy195 three; Durability3512/Agility3818 three each;
Sturdy1403 one (raw AC). High-risk burns/executes/refills, charged and grant-only
veteran families remain deferred. Class/race masks, prices and prerequisites
remain. Existing out-of-pool ranks stay stored/dormant, with charges, wallets
and spent accounting preserved; legal earned ranks restore without rebuying.

At creation WAR/CLR/WIZ has152 visible families/389 closed ranks/1692 points;
MAG/NEC/SHM143/348/1506; PAL/WAR/MNK140 visible families,139 purchase-closed
families/353 ranks/1491 points. Coverage is unchanged through level50. These
are catalog ceilings, not measured fight strength. A class-dependent prerequisite
can still block a visible family for a particular union.

Six policy tests (including all DB levels255),5646 native rank/level cases plus
actual purchase/save/projection checks,13 deployment and7 notes-publication
tests pass. Both policy and native checks reproduced the previous failure.
Independent review verified unchanged rank identities, retained source/link
inputs and ownership; only aa.cpp and its generated header changed. The earlier
trainer/skill/offhand correction is retained. Existing ownable ranks are still
reprojected on login, refresh and level changes; no blanket buff purge occurs.

Only zone needs rebuilding/restarting; generic AA/rules reload cannot install
the compiled policy. Use guarded whole-runtime rollout, fresh backups and
image-only recovery against current player data, never old SQL. Pet HP changes
on summon/restore; resummon for HP QA. Avoidance/AC reads current owner bonuses.
Signed game notes2026101302 preserve all105 client file records and prior history;
no client binary change. Original level-gated evidence is historical/superseded.
No new encounter campaign or player enjoyment acceptance is claimed.'''
    texts['references/balance.md']=section(texts['references/balance.md'],'## Buried Sea AA policy','## Source routes',balance)
    multi=f'''## AA catalog policy — all allowed ranks at level 1

The owner rejected character-level AA gates October13. Every allowed AA and rank
opens at creation: choices, points and prerequisites govern purchasing. The same
390-family/941-rank TBS pool, six exceptions and numeric release ceilings remain.
See [balance](balance.md) and `{ROOT.as_posix()}/docs/releases/aa-tbs-level1-20261013/README.md`.
Native packet requirements are1; CanUse/CanPurchase/default grants ignore DB
level_req for clients. Explicit GM grant content filters remain optional.

Canonical earned ranks, charges, wallets/spent totals survive; out-of-pool ranks
remain dormant. ReprojectEarnedAAs restores legal earned ranks without repurchase;
level changes no longer shrink that prefix. Class release still changes access.
Clear/table/points/stats refresh and missing-prerequisite rejection remain.
Zone-only correction is live on all12 OVH zones, retaining the skill/offhand
build. No new client binary; signed notes2026101302 preserve105 hosted assets.
All239 purchase rows and47 player/11 custom tables preserved. Exact native tests
and independent review passed; corrected creation/purchase/pet/combat owner QA
and main promotion remain pending. Pet HP updates on summon/restore.'''
    texts['references/multiclass.md']=section(texts['references/multiclass.md'],'## AA catalog policy','## Skills and AA ownership',multi)
    client='''## AA notes-only publication October 13

Signed game release2026101302 publishes the Buried Sea summary and correction
restoring all allowed AA ranks at creation. It preserves the105 existing file
records including URLs, prior patch history, minimum launcher0.6.0, desktop,
starter and guide. No client binary update. A higher game metadata counter may
reuse previous release asset URLs: verify exact signed file records, not an
assumption that URL counter must equal manifest counter. Source and public HTTPS
receipt: docs/releases/aa-tbs-level1-20261013/{sign-notes.go,publish-notes.py,
hosted-notes-verification.json} in the AA policy worktree. The paired server
correction is live; native AA-window and purchase owner QA remain pending.

'''
    if '## AA notes-only publication October 13' not in texts['references/client.md']:
        texts['references/client.md']=texts['references/client.md'].replace('## High-value implementation pointers',client+'## High-value implementation pointers')
    manifest=json.loads(texts['references/sources.json'])
    manifest['observed_revisions']['aa_tbs_level1_20261013']=revision
    manifest['basis']+=' October13 owner correction replaces character-level AA gates with level1 access; deployment/signature evidence verified, gameplay QA pending.'
    common=['AGENTS.md','config/aa-policy.json','server-mods/code/common/nightcap_aa_policy.h','server-mods/code/zone/aa.cpp','tools/aa_tbs_policy.py','tools/tests/test_aa_tbs_policy.py','tools/tests/verify_aa_tbs_native.py','tools/build_aa_level1_candidate.py']
    evidence=['README.md','build-manifest.json','verification.json','server-receipt.json','post-notes-health.json']
    for topic in ('balance','multiclass','client'):
        entries=manifest['topics'][topic]
        for entry in entries:
            if entry['root']==ROOT.as_posix() and (ROOT/entry['path']).is_file():
                entry.update(revision=revision,sha256=sha((ROOT/entry['path']).read_bytes()))
        additions=common+[f'docs/releases/aa-tbs-level1-20261013/{n}' for n in evidence] if topic!='client' else ['eq-launcher/patch-notes.json']+[f'docs/releases/aa-tbs-level1-20261013/{n}' for n in ['sign-notes.go','publish-notes.py','hosted-notes-verification.json']]
        for path in additions:
            row=dict(root=ROOT.as_posix(),path=path,role='Reviewed level-1 AA correction or signed publication evidence; owner QA pending',revision=revision,sha256=sha((ROOT/path).read_bytes()))
            i=next((i for i,e in enumerate(entries) if e['path']==path),None)
            if i is None:entries.append(row)
            else:entries[i]=row
    texts['references/sources.json']=json.dumps(manifest,indent=2)+'\n'
    changes=[]
    for name in paths:
        changes.extend(difflib.unified_diff(before[name].decode('utf-8').splitlines(True),texts[name].splitlines(True),fromfile=str(SKILL/name),tofile=str(SKILL/name)))
    (HERE/'nightcap-skill-update.patch').write_text(''.join(changes),encoding='utf-8',newline='\n')
    assert all((SKILL/n).read_bytes()==raw for n,raw in before.items()),'Concurrent knowledge update'
    for name in paths:
        target=SKILL/name;temp=target.with_name(target.name+'.aa-level1.tmp')
        with temp.open('xb') as f:f.write(texts[name].encode('utf-8'))
        os.replace(temp,target)
    receipt={'installed':True,'revision':revision,'files':{n:{'before':sha(before[n]),'after':sha(texts[n].encode())} for n in paths}}
    (HERE/'skill-update-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))

if __name__=='__main__':main()
