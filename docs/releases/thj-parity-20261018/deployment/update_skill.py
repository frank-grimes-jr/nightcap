"""Replace candidate status with verified deployment and retain scoped source pins."""
import difflib
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
PREFIX='docs/releases/thj-parity-20261018/'
DEP=PREFIX+'deployment/'
HEADING='## Combined THJ item/spell and pet/WPM deployed — October 18, 2026'
LOCATION=f'''Source: {ROOT.as_posix()}. Owner-authorized main/OVH deployment is verified in
`{DEP}README.md` and `receipts/`. PR235 promotes the tested source;
signed client2026101802/proxy0.11.0 and wiki20261018-thj-parity-v1 are published
and verified. Classic50 remains active; level65/PoP and389 stock additions stay
staged. Owner gameplay and balance acceptance remain open. Exact testing:
`{PREFIX}QA.md`; measured limitations: `COMPARISON.md`.
'''


def main():
    deployed=json.loads((HERE/'receipts/deployed.json').read_text(encoding='utf-8'))
    hosted=json.loads((HERE/'hosted-verification.json').read_text(encoding='utf-8'))
    public=json.loads((HERE/'wiki-public-verification.json').read_text(encoding='utf-8'))
    assert deployed['gateway_open'] and hosted['hosted'] and public['result']=='PASS'
    spec=importlib.util.spec_from_file_location('candidate_skill',HERE.parent/'update_skill.py')
    candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
    blocks={k:v for k,v in candidate.BLOCKS.items() if k in ('balance','items')}
    blocks['balance']=blocks['balance'].replace('reviewed candidate SQL enables them separately.','deployed SQL enables them separately.').replace('the unchanged paired\nfive-file NCPA2 client delta','the signed five-file NCPA2 update over the full138-file inventory')
    blocks['items']+='''
Production installed all1393 full-row afterimages, matching caches and the paired
native image. Three rule-note strings now match compiled ruletypes.h because
world normalizes them on startup. Forward/disable/enable guards were rehearsed
on the retained public clone after that normalization; no live SQL repair was
needed. Keep numeric recovery separate from effects, sockets and owned state.
'''
    blocks['operations']=f'''Production stage /opt/nightcap/releases/thj-parity-20261018 runs the full
reviewed image {deployed['runtime']['image_id']}.
All12 zones, world and shared_memory match native-build-manifest.json;119 source
overlays retain the cooldown/auth/reforge base. Ten guarded content components,
regenerated item/spell caches and signed138-file client are verified. A fresh
stopped64,405,100-byte compressed backup passed integrity. {deployed['player_tables']} player and
{deployed['custom_tables']} custom-table receipts preserve owned state without restoration.
Game/gateway are open and healthy; db/web/tunnel were preserved. Final disk
headroom was3.6GiB; retain recovery artifacts and check capacity before later builds.

The first boot held access only because RuleManager::UpdateInjectedRules
(retained common/rulesys.cpp) replaced three descriptions with compiled notes;
values and other content matched. resume_rule_notes.py authenticates exactly
those transitions and rehearses ten corrected recovery/reapply checks on the
public clone. No production SQL replay or player snapshot restoration occurred.
Use resume_pinned.py for a retained restart: it authenticates/reselects the new
immutable image under both deployment/GM locks before recovery.resume(). The
original rollout.py open is not valid for this reviewed hold. Recovery open
requires all138 HTTPS assets verified by the shipped-key manifest parser.
Both market startup epochs are authenticated independently. New holds need a
fresh diagnosis. Existing procedure remnants must be inspected before retry.

New rules require paired world/zone; regenerate both caches and use a supported
full runtime restart. Do not revert to the older eight-location pet binary or
delete earned AA content while new state is owned. Formula disable/enable and
numeric recovery preserve sockets/effects/owned data. Exact operator source,
29 regression groups, content rehearsal and deployed receipts are in deployment/.
Native47-case and165-test evidence remains distinct from player acceptance.
'''
    blocks['wiki']='''All21 maintained guides and432 generated reward routes were reviewed.
Fifteen guides now describe released item/spell/starter/dungeon and pet/WPM
mechanics with Live testing status. Features/home/Recent changes, commands,
equipment/combat/pets and progression boundaries agree. Hunt catalog IDs do not
intersect the1393 changed definitions, so its384 published item values remain
unchanged; no command/acquisition rewrite was needed. Separate PoP65/389-stock
and quest-guarantee proposals remain unreleased.

Wiki20261018-thj-parity-v1 supersedes20261018-loot-quality-v1. The guarded updater
rehearsed rollback, retained Nginx/private downloads/all5 service identities and
needed no reload. All465 public file hashes/security headers and five private
source-route denials pass. Thirty Linux wiki/deploy/update/refresh tests and13
Node checks passed. Receipts and whole-wiki decisions are in deployment/;
check_refresh.py compares the actual current source and working changes. The
private source ledger is excluded from public payloads. Publication is verified;
owner gameplay/balance acceptance is still open.
'''
    updates={}
    for topic in ('balance','items','operations','wiki','client','multiclass'):
        p=SKILL/'references'/f'{topic}.md';old=p.read_text(encoding='utf-8')
        marker=candidate.HEADING if candidate.HEADING in old else candidate.OLD
        a=old.index(marker);b=old.find('\n## ',a+len(marker));assert b>=0
        if topic not in blocks:
            body=old[a:b].split('\n\n',2)[2]
            if topic=='client':
                body=body.replace('with candidate\nserver/schema/cache/AA policy','with deployed\nserver/schema/cache/AA policy')
                body=body.replace('The five-file delta is unsigned/uninstalled and requires the current signed\nbase, including October18 travel assets.', 'Signed game2026101802 publishes the five-file delta over the complete138-file\n2026101801 base, preserving all133 other assets and patch history. All138 HTTPS\nbytes, sizes and shipped-key signatures verify in deployment/hosted-verification.json.')
                body=body.replace('Evidence: current client-stage.json and native/unit tests, not visible QA proof.','Evidence: client-stage.json, signed publication receipts and native/unit tests;\nthese are not visible QA proof. No protected reference-client edits occurred.')
            blocks[topic]=body
        updates[p]=(old,old[:a]+HEADING+'\n\n'+LOCATION+'\n'+blocks[topic].strip()+'\n\n'+old[b+1:])
    p=SKILL/'references/sources.json';old=p.read_text(encoding='utf-8');data=json.loads(old)
    revision=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()+' + reviewed deployment working tree'
    data['observed_revisions']['thj_combined_deployed_20261018']='1039fdd007beb090f2830c2b546b77432c0ab0b6; '+revision
    data['basis']+=' October18 combined THJ/pet/WPM deployed via PR235: paired runtime,1393 item afterimages, signed2026101802 all138 assets and wiki465 files verified; exact rule-note startup normalization recovered forward with owned state preserved. Classic50 retained; gameplay/balance acceptance open.'
    companion=candidate.REL.joinpath('companion-final-snapshot.json')
    companion=json.loads(companion.read_text(encoding='utf-8'))['source'].replace('\\','/')
    paths={k:list(v) for k,v in candidate.PATHS.items()}
    for topic in ('client','multiclass'):
        paths[topic]=[r['path'] for r in data['topics'][topic] if r['root'].replace('\\','/')==companion]
    paths['operations'] += [DEP+n for n in ('README.md','rollout.py','resume_rule_notes.py','resume_pinned.py','test_rollout.py','test_rule_notes.py','receipts/deployed.json','receipts/report.json')]
    paths['client'] += [DEP+n for n in ('publish_client.py','test_publish_client.py','hosted-verification.json')]
    paths['client'] += ['eq-launcher/patch-notes.json']
    paths['wiki'] += [DEP+n for n in ('wiki-review.json','wiki-publication.json','wiki-public-verification.json')]
    count=0
    for topic,names in paths.items():
        names=sorted(set(names));entries=data['topics'][topic]
        entries[:]=[r for r in entries if not(r['root'].replace('\\','/') in (ROOT.as_posix(),companion) and r['path'] in names)]
        for name in names:
            entries.append(dict(root=ROOT.as_posix(),path=name,role='Reviewed combined THJ/pet/WPM deployment; owner gameplay QA open',revision=revision,sha256=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()))
            count+=1
    updates[p]=(old,json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    patch=''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=p.as_posix(),tofile=p.as_posix())) for p,(a,b) in updates.items())
    with (HERE/'skill-update.patch').open('x',encoding='utf-8') as f:f.write(patch)
    for p,(old,_) in updates.items():assert p.read_text(encoding='utf-8')==old,'Concurrent skill edit'
    for p,(_,new) in updates.items():p.write_text(new,encoding='utf-8')
    report={'status':'installed','files':list(map(str,updates)),'reviewed_source_entries':count,'source_revision':revision,'deployment':'verified; owner QA open'}
    (HERE/'skill-maintenance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
