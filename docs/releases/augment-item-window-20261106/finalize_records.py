"""One-shot reconcile of verified live receipts and their exact public source."""
import difflib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PUBLIC=ROOT/'artifacts/augment-item-window/wiki-source/wiki'


def main():
    deployed=json.loads((HERE/'deployed.json').read_text())
    client=json.loads((HERE/'client-public-verification.json').read_text())
    wiki=json.loads((HERE/'wiki-publication.json').read_text())
    assert deployed['gateway_open'] and not deployed['cache_changed'] and deployed['command_access']==0
    assert client['release']==2026110601 and client['hosted'] and client['changed_assets']==2
    assert wiki['result']=='PASS' and wiki['files']==510
    for slug in ('augment-audit','equipment','commands','features','recent-changes'):
        path=ROOT/'wiki/articles'/(slug+'.json')
        current=json.loads(path.read_text(encoding='utf-8'))
        public=json.loads((PUBLIC/'articles'/path.name).read_text(encoding='utf-8'))
        anchor='<h2 id="augment-description-correction">'
        start=current['body'].index(anchor)
        public_anchor=anchor if anchor in public['body'] else '<p id="augment-description-correction">'
        public_start=public['body'].index(public_anchor)
        current['body']=current['body'][:start]+public['body'][public_start:]
        current['reviewed_at']='2026-11-06'
        path.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    diff=[]
    for path in sorted(PUBLIC.rglob('*')):
        rel=path.relative_to(PUBLIC)
        if not path.is_file() or rel.parts[0] in ('dist','__pycache__'):
            continue
        if not (rel.parts[0]=='articles' and path.suffix=='.json' or rel.as_posix() in ('build.py','catalog.py','catalog.json','chapterhouse_catalog.py','augment_candidate.py','augment-candidate.json')):
            continue
        base=ROOT/'wiki'/rel
        before=base.read_text(encoding='utf-8') if base.exists() else ''
        after=path.read_text(encoding='utf-8')
        diff.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/wiki/'+rel.as_posix(),tofile='b/wiki/'+rel.as_posix()))
    (HERE/'published-source-overrides.patch').write_text(''.join(diff),encoding='utf-8')
    p=ROOT/'docs/status.md';s=p.read_text(encoding='utf-8');a=s.index('## November6 follow-up');b=s.index('\n## ',a+5)
    s=s[:a]+'''## November6 follow-up — augment descriptions/totals live; owner QA open

Main PR408/3343d6c8 is deployed on OVH; access is open. The self-only #augstats
report shows actual equipped Shield Block, Shielding and other combat totals,
current caps/headroom and stacking. No item power, drops or cache changes.
Signed client2026110601/proxy0.13.3 is published: all148HTTPS assets/signature/pair
verified;146unrelated assets preserved. Fully EXIT EQ/use launcher Play for
normal item Description text showing +1% Polished/Exalted and +2% Ascension Hunt
shield block, worn-socket/shield requirements and strongest-only stacking.

Wiki20261106-augment-description-v1 passed510-file publication, private-download/
service preservation and rollback checks. [Details and exact native QA](releases/augment-item-window-20261106/README.md).
Native visible/gameplay acceptance remains open; isolated native text checks
and delivery verification are separate from owner acceptance.
''' + s[b:];p.write_text(s,encoding='utf-8')
    p=ROOT/'CHANGES.md';s=p.read_text(encoding='utf-8').replace('# CHANGES\n','''# CHANGES

## 2026-11-06 — Augment descriptions and equipped totals deployed

Deploy the owner-requested live-QA correction from main PR408: #augstats provides
self-only server-calculated equipped totals/caps; signed client2026110601/0.13.3
shows Hunt Shield Block in normal item Description with restrictions/stacking.
Stopped backup, saved-state/content/cache/native checks and reopened access pass.
All148hosted client assets/signature/pair verified; only DLL/catalog changed,
146assets preserved. No item power, drop, rule or inventory migration. Fully
exit EQ/use launcher Play; relogging cannot replace the loaded DLL. The native
stock250healing cap label is not server truth. Wiki510files/rollback/private
downloads/services verified. Owner visible/gameplay acceptance remains open.
Evidence: `docs/releases/augment-item-window-20261106/`.
''',1);p.write_text(s,encoding='utf-8')
    p=HERE/'README.md';s=p.read_text(encoding='utf-8');s+='''
## Verified deployment and publication

Main PR408 merged as3343d6c8bb9c2d1c66de3e68c1c01309479838f6. All one-shot
preflight/activate/open jobs succeeded. `deployed.json` is a fresh independent
readback: zone3fc2b901, healthy reopened gateway, exact unchanged item cache,
content/rules and all prior command rows; only player-access augstats row added.
Stopped backup65580990compressed/471046452uncompressed bytes passed gzip checks,
SHA256 b2504e29c02bb2b748335ef2bf90f25327e10e59a4d427dc89fb5115cbea68a4.
Saved-state model/market rotation were verified before access reopening; no old
player snapshot was restored. World/shared_memory and compatible metadata retained.

`client-published.json` and `client-public-verification.json` verify signed
2026110601/proxy0.13.3: all148hosted assets/300608073bytes, production signature,
DLL/catalog pair, history and146unchanged assets/URLs. Fully exit EQ/use Play.
The client update does not change game power, item names, spell definitions or
player INIs. Twenty POSIX publisher/recovery tests passed before publication.

`wiki-publication.json` records20261106-augment-description-v1:510files/503HTML
routes, exact hashes, private downloads, unchanged service identities/start times,
atomic rollback rehearsal. Five owning guide/Features/Change Log instructions
were updated; all item/zone/catalog/Build Lab/asset data is preserved. Main plus
`published-source-overrides.patch` reproduces actual public source while keeping
unrelated source-only previews distinct. Global historical wiki drift remains
REVIEW REQUIRED; no blind ledger advancement. Public-scope/link/stacking tests pass.

Rollback before reopening uses the held native operator and compatible prior
augment image; no player restore. After reopening, use a fresh compatible forward
repair. Client recovery uses a newly signed higher counter with a matching DLL/
catalog pair and preserved current assets; never lower counters or reset history.
The prior proxy remains compatible with #augstats if only its description hook
needs reversal. Native pixel/skin/socket/link and gameplay acceptance remains
owner live QA; automated rendering/delivery checks do not establish acceptance.
''';p.write_text(s,encoding='utf-8')
    p=ROOT/'docs/README.md';s=p.read_text(encoding='utf-8').replace('# Nightcap documentation\n','# Nightcap documentation\n\n- [Augment Description and equipped totals: deployed correction and exact QA](releases/augment-item-window-20261106/README.md)\n',1);p.write_text(s,encoding='utf-8')
    p=HERE/'review.json';d=json.loads(p.read_text());d['publication']='OVH native, signed2026110601/all148assets and wiki510files verified';d['status']='deployed for live QA; owner native visual/gameplay acceptance remains open';p.write_text(json.dumps(d,indent=2)+'\n')
    p=HERE/'wiki-impact.json';d=json.loads(p.read_text());d['publication']='verified20261106-augment-description-v1;510files, rollback/private downloads/services pass';p.write_text(json.dumps(d,indent=2)+'\n')
    print('Recorded verified native/client/wiki release; preserved unrelated main-only previews.')


if __name__=='__main__':main()
