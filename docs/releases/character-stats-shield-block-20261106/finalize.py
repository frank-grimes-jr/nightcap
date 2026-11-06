"""Record the verified single Shield Block display and reviewed knowledge."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PUBLIC=ROOT/'artifacts/character-stats-shield-block/wiki-source/wiki'
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development/references')


def main():
    client=json.loads((HERE/'client-public-verification.json').read_text())
    published=json.loads((HERE/'client-published.json').read_text())
    wiki=json.loads((HERE/'wiki-publication.json').read_text())
    source=json.loads((HERE/'source-merge.json').read_text())
    assert client['release']==2026110604 and client['hosted'] and client['changed_assets']==1
    assert published['services_before']==published['services_after']
    assert wiki['result']=='PASS' and wiki['files']==510 and wiki['service_ids_start_times_preserved']
    # Record the actual public source separately from unrelated main previews.
    diff=[];inputs=[]
    for p in sorted(PUBLIC.rglob('*')):
        rel=p.relative_to(PUBLIC)
        if not p.is_file() or not (rel.parts[0]=='articles' and p.suffix=='.json' or rel.as_posix() in
            ('build.py','catalog.py','catalog.json','chapterhouse_catalog.py','augment_candidate.py','augment-candidate.json')):continue
        inputs.append(rel);base=ROOT/'wiki'/rel
        before=base.read_text(encoding='utf-8') if base.exists() else ''
        diff.extend(difflib.unified_diff(before.splitlines(True),p.read_text(encoding='utf-8').splitlines(True),
                    fromfile='a/wiki/'+rel.as_posix(),tofile='b/wiki/'+rel.as_posix()))
    patch=HERE/'published-source-overrides.patch';patch.write_text(''.join(diff),encoding='utf-8',newline='\n')
    rep=ROOT/'artifacts/character-stats-shield-block/reproduced';rep.mkdir()
    shutil.copytree(ROOT/'wiki',rep/'wiki',ignore=shutil.ignore_patterns('dist','__pycache__'));shutil.copytree(ROOT/'config',rep/'config')
    for rel in inputs:
        p=rep/'wiki'/rel
        if p.exists():p.write_text(p.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
    subprocess.run(['git','apply','--directory=artifacts/character-stats-shield-block/reproduced',str(patch)],cwd=ROOT,check=True)
    for rel in inputs:assert (rep/'wiki'/rel).read_text(encoding='utf-8')==(PUBLIC/rel).read_text(encoding='utf-8'),rel
    subprocess.run(['python',str(rep/'wiki/build.py')],check=True)
    hashes=lambda folder:{p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
    assert hashes(rep/'wiki/dist')==hashes(PUBLIC/'dist')
    (HERE/'public-source-reproduction.json').write_text(json.dumps(dict(status='PASS',source_inputs=len(inputs),files=510,
        method='main source and recorded overrides normalized to LF reproduce exact public outputs'),indent=2)+'\n')
    p=HERE/'README.md';text=p.read_text(encoding='utf-8');text+=f'''
## Verified publication

Main PR{source['number']}/{source['mergeCommit']['oid']} is published as signed
2026110604/proxy0.13.4. Signature, all148descriptors/history and served changed XML
plus retained DLL/catalog verify. Publisher hashes all147retained files; all five
service identities/starts/restarts are unchanged. HTTPS scope is3files, not a
repeated download of unchanged files. No server/DLL/restart/player-data change.
20Linux publisher fault tests and7UI/3public-scope tests pass. Wiki510files,
{wiki['preserved_files']}preserved, rollback/private/service guards pass. Recorded overrides
reproduce79source inputs/510outputs. Historical global drift stays review-required.
Owner previously reports Stats functioning; revised display pixels remain QA.
Exit EQ/use launcher Play to load the XML update.
''';p.write_text(text,encoding='utf-8')
    p=ROOT/'CHANGES.md';text=p.read_text(encoding='utf-8').replace('Single Shield Block display candidate','Single Shield Block display published',1).replace(
        'Publication and owner revised-display QA pending.','Publication verified:148signed descriptors, served XML/pair,147retained hashes,\nunchanged services and wiki510files. Owner revised-display QA remains open.',1);p.write_text(text,encoding='utf-8')
    p=ROOT/'docs/status.md';text=p.read_text(encoding='utf-8').replace('single Shield Block display candidate','single Shield Block display published',1).replace(
        'Candidate2026110604 removes','Published2026110604 removes',1).replace('Native/DLL/runtime unchanged; no restart.',
        'Signature/148descriptors/served XML+pair and147retained hashes verify; wiki510files\nand unchanged services pass. Native/DLL/runtime unchanged; no restart.',1);p.write_text(text,encoding='utf-8')
    p=HERE/'wiki-impact.json';o=json.loads(p.read_text());o['publication']=f"verified20261106-character-stats-shield-block-v1;510files,{wiki['preserved_files']}preserved; rollback/private/service guards pass";p.write_text(json.dumps(o,indent=2)+'\n')
    p=ROOT/'docs/README.md';text=p.read_text(encoding='utf-8').replace('# Nightcap documentation\n','# Nightcap documentation\n\n- [Single Shield Block display: publication and QA](releases/character-stats-shield-block-20261106/README.md)\n',1);p.write_text(text,encoding='utf-8')
    old={n:(SKILL/n).read_text(encoding='utf-8') for n in ('client.md','items.md','operations.md','wiki.md','sources.json')};new=dict(old)
    client_text='''## Character Stats — November6 single Shield Block total published

Current source E:/EQ_Local_Dev/_worktrees/character-stats-shield-block;
docs/releases/character-stats-shield-block-20261106/ owns publication, preservation,
source reproduction and exact QA. Signed2026110604/proxy0.13.4 changes Inventory
XML only;147other asset descriptors/URLs, DLL/catalog/config, recall/cast-bar
fixes, history and tombstones retained. No native build/restart/player change.
Signature/all148descriptors and served changed XML plus retained DLL/catalog
verify. Publisher hashes all147retained files and preserves all five service
identities/start times/restarts. HTTPS scope is3files, not a repeated148download.
Fully EXIT EQ/use launcher Play; protected reference client untouched.

Owner explicitly requests plain Shield Block. Keep ONE total row, EQType10200,
including equipped augment bonuses. Remove NCST_Row1/Name1/Value1 and tile
reference; do not rename the breakdown to create duplicate labels. No Hunt,
contribution, augment-only or max row in the normal Stats view. Shielding remains
separate melee reduction. Tooltip explains shield requirement, frontal/counter
limits, inclusion of augments and strongest augment block only. Stacking/combat
unchanged. Internal source identifiers and compatibility fields may remain;
do not expose implementation names in normal player UI.

tools/client_character_stats_ui.py::show_total_shield_block scopes live XML and
compacts the tile/focus section: exactly3controls removed,4owning controls changed,
all others retained. match_character_stats_font inherits IWS_Shielding Font,
including absent/default,14px height and75px values; never pin Font2. Server mod
totals/caps, Shield Block, relative Dodge, worn-item focus potential/Faerune
refresh automatically. Focus is best worn-item potential before spell limits;
buffs/AAs may alter casts. Damage/healing use750base caps plus earned headroom.
#augstats remains the detailed diagnostic fallback; no command is required.

Native ea6ad532 baseline (PR410), compatible world/shared_memory, rules/cache/
ItemData/Client layout unchanged. [NCST1] keeps33int32fields, existing generation/
character/zone/instance/spawn identity, replay sequence and8second expiry; stale
data shows --. Existing Label/Chat/State hooks and120native guards unchanged.
Silent self-only polls at most1/sec while rendered, existing server3sec throttle,
no DB query/RNG/focus consumption or GM quest callbacks/log spam. Eligible worn
items/augs only, no bags/ordinary slot21training; passive cast level is not an
equip requirement. Original native/hook/collection/cache tests and build receipts:
character-stats-window-20261106; font evidence: character-stats-font-20261106.

Owner reports Stats functioning. Revised font/single-row pixels, scrolling,
resize and broader class/zone lifecycle/gameplay QA remain open.7UI tests,
structural scope,20Linux publisher/recovery and3public-scope/link tests pass.
Item Description annotation remains; item names/spells/power unchanged. Current
topic character-stats-display pins reviewed source/evidence. Prior topics retain
dated native/font release scope. Delivery is separate from owner acceptance.
'''
    a=old['client.md'].index('## Character Stats and augment descriptions');b=old['client.md'].index('\n## ',a+3)
    new['client.md']=old['client.md'][:a]+client_text.rstrip()+'\n'+old['client.md'][b:]
    new['items.md']=new['items.md'].replace('signed2026110603/proxy0.13.4','signed2026110604/proxy0.13.4').replace('Shield Block/Hunt aug block,','A single Shield Block total,')
    new['operations.md']=new['operations.md'].replace('Current signed0.13.4/2026110603 is an XML-only font/label correction;147assets','Current signed0.13.4/2026110604 is an XML-only single Shield Block display;147assets').replace('including DLL/catalog retained, all148HTTPS assets verify.','including DLL/catalog retained;148signed descriptors/3served files verify.').replace('See character-stats-font release receipts.','See character-stats-shield-block release receipts.')
    heading='## Zone augments and character Stats — November6 published; native QA open'
    a=new['wiki.md'].index(heading);b=new['wiki.md'].find('\n## ',a+3)
    if b<0:b=len(new['wiki.md'])
    wiki_text='''## Zone augments and character Stats — November6 published; native QA open

Current wiki20261106-character-stats-shield-block-v1 replaces the font release.
510files/503HTML routes,504preserved; rollback/private-download/service identity/
start checks pass. Five owning guide/Features/Change Log instructions now use
one Shield Block total including equipped augments, separate Shielding and
unchanged strongest-only augment stacking. Remove redundant Hunt/contribution
row from current instructions; retain dated historical release notes. Generated
item/zone/catalog values, Home/navigation, Build Lab/assets and gameplay unchanged.
Owner reports Stats functions; revised display and broader gameplay QA open.

Source E:/EQ_Local_Dev/_worktrees/character-stats-shield-block,
docs/releases/character-stats-shield-block-20261106/ owns scope/publication, source
overrides and79input/510output reproduction. Main retains unrelated unpublished
previews; never publish wholesale. Historical drift stays REVIEW REQUIRED, no
blanket advancement. Native ea6ad532 unchanged; signed2026110604/proxy0.13.4 XML
verifies148descriptors, served XML/retained pair, all147retained hashes at publish.
No restart. Topic character-stats-display pins reviewed current evidence.
'''
    new['wiki.md']=new['wiki.md'][:a]+wiki_text.rstrip()+'\n'+new['wiki.md'][b:]
    manifest=json.loads(new['sources.json']);revision=source['mergeCommit']['oid']+' plus verified single-total publication records'
    paths=['tools/client_character_stats_ui.py','tools/tests/test_client_character_stats.py']
    paths+=['docs/releases/character-stats-shield-block-20261106/'+n for n in ('README.md','ui-audit.json','source-merge.json','verify_public.py','client-public-verification.json','client-published.json','wiki-publication.json','wiki-impact.json','published-source-overrides.patch')]
    entries=[dict(root=ROOT.as_posix(),path=p,role='Reviewed single Shield Block total; owner function reported, revised display QA open',revision=revision,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths]
    manifest['topics']['character-stats-display']=entries;manifest['observed_revisions']['character_stats_single_total_20261106_published']=revision
    for topic in ('client','items','operations','wiki'):
        manifest['topics'][topic]+=[e for e in entries if e['path'].endswith(('README.md','client-public-verification.json','wiki-publication.json'))]
    new['sources.json']=json.dumps(manifest,indent=2)+'\n'
    patch=''.join(''.join(difflib.unified_diff(old[n].splitlines(True),new[n].splitlines(True),fromfile='a/references/'+n,tofile='b/references/'+n)) for n in new)
    (HERE/'installed-skill-update.patch').write_text(patch,encoding='utf-8',newline='\n')
    for n,text in new.items():(SKILL/n).write_text(text,encoding='utf-8',newline='\n')
    (HERE/'skill-maintenance.json').write_text(json.dumps(dict(status='applied',reviewed_entries=len(entries),revision=revision),indent=2)+'\n')
    print('Verified single Shield Block release and skill fingerprints recorded.')


if __name__=='__main__':main()
