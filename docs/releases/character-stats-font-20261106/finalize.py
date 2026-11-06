"""Record verified XML-only publication and the owner's limited function report."""
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PUBLIC=ROOT/'artifacts/character-stats-font/wiki-source/wiki'
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development/references')


def main():
    client=json.loads((HERE/'client-public-verification.json').read_text())
    published=json.loads((HERE/'client-published.json').read_text())
    wiki=json.loads((HERE/'wiki-publication.json').read_text())
    source=json.loads((HERE/'source-merge.json').read_text())
    assert client['release']==2026110603 and client['hosted'] and client['changed_assets']==1
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
    rep=ROOT/'artifacts/character-stats-font/reproduced';rep.mkdir()
    shutil.copytree(ROOT/'wiki',rep/'wiki',ignore=shutil.ignore_patterns('dist','__pycache__'));shutil.copytree(ROOT/'config',rep/'config')
    for rel in inputs:
        p=rep/'wiki'/rel
        if p.exists():p.write_text(p.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
    subprocess.run(['git','apply','--directory=artifacts/character-stats-font/reproduced',str(patch)],cwd=ROOT,check=True)
    for rel in inputs:assert (rep/'wiki'/rel).read_text(encoding='utf-8')==(PUBLIC/rel).read_text(encoding='utf-8'),rel
    subprocess.run(['python',str(rep/'wiki/build.py')],check=True)
    hashes=lambda folder:{p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
    assert hashes(rep/'wiki/dist')==hashes(PUBLIC/'dist')
    (HERE/'public-source-reproduction.json').write_text(json.dumps(dict(status='PASS',source_inputs=len(inputs),files=510,
        method='main source and recorded overrides normalized to LF reproduce exact public outputs'),indent=2)+'\n')
    p=HERE/'README.md';text=p.read_text(encoding='utf-8');text+=f'''
## Verified release

Main PR{source['number']}/{source['mergeCommit']['oid']} is published as signed
2026110603/proxy0.13.4. All148HTTPS assets/{client['verified_bytes']}bytes, shipped-key
signature, history and retained DLL/catalog pair verify. Only Inventory XML changed;
147other descriptors/URLs retained. All five service identities/starts/restarts
are unchanged.20Linux publisher fault tests passed. Wiki20261106-character-stats-font-v1
verifies510files/503HTML routes, rollback/private downloads/service preservation;
{wiki['preserved_files']}files preserved. Main plus recorded overrides reproduces79inputs/510outputs.
The inherited global wiki source drift remains review-required, not blanket approved.

Owner reports Stats functioning in their screenshot. The revised font/row sizing,
scrolling/resize and broader lifecycle/gameplay checks remain open. Full EQ exit/
launcher Play loads the new XML; no native server restart or DLL replacement.
''';p.write_text(text,encoding='utf-8')
    p=ROOT/'CHANGES.md';text=p.read_text(encoding='utf-8').replace('Character Stats font correction candidate','Character Stats font correction published',1)
    text=text.replace('Revised pixel QA is open; publication pending.','All148hosted assets/signature/pair verify;147preserved. All service identities/starts\nremain. Wiki510files/rollback/private routes verify. Revised pixel QA is open.',1);p.write_text(text,encoding='utf-8')
    p=ROOT/'docs/status.md';text=p.read_text(encoding='utf-8').replace('Stats function reported; font correction candidate','Stats function reported; font correction published',1)
    text=text.replace('Signed2026110603 is an XML-only candidate; proxy0.13.4 and native runtime unchanged.','Signed2026110603 is published/verified: Inventory XML only;147assets and proxy0.13.4\nretained. All148HTTPS hashes/signature/pair verify, wiki510files/private guards pass.\nNative runtime/services were not restarted.',1);p.write_text(text,encoding='utf-8')
    p=HERE/'wiki-impact.json';o=json.loads(p.read_text());o['publication']=f"verified20261106-character-stats-font-v1;510files,{wiki['preserved_files']}preserved, rollback/private/service guards pass";p.write_text(json.dumps(o,indent=2)+'\n')
    p=ROOT/'docs/README.md';text=p.read_text(encoding='utf-8').replace('# Nightcap documentation\n',
        '# Nightcap documentation\n\n- [Stats font correction and Hunt augment block explanation](releases/character-stats-font-20261106/README.md)\n',1);p.write_text(text,encoding='utf-8')
    # Replace superseded current client delivery guidance, retaining the native baseline.
    old={n:(SKILL/n).read_text(encoding='utf-8') for n in ('client.md','items.md','operations.md','wiki.md','sources.json')};new=dict(old)
    new['client.md']=new['client.md'].replace('Signed2026110602/proxy0.13.4 changes DLL, paired catalog and Inventory XML only;\n145 descriptors/URLs and signed history/tombstones/config, recall/cast-bar repairs\nretained.',
        'Current signed2026110603/proxy0.13.4 changes Inventory XML only;147descriptors/URLs,\nDLL/catalog, history/tombstones/config and recall/cast-bar repairs retained.\nThe preceding2026110602 introduced the paired DLL/catalog and Stats XML.')
    new['client.md']=new['client.md'].replace('Owner visible sizing/scroll/refresh and gameplay acceptance remains live QA.',
        'Owner reports the Stats view functions (November6 screenshot); revised font\npixels/scroll/resize and broader zone/class lifecycle/gameplay QA remain open.')
    marker='Context topic character-stats pins the reviewed current source and receipts.'
    new['client.md']=new['client.md'].replace(marker,marker+'''

Font correction: tools/client_character_stats_ui.py::match_character_stats_font
inherits Font (including absent/default) and14px height from IWS_Shielding;
never force Font2 on added Stats labels. Values use75px. Hunt aug block replaces
the confusing Hunt contribution label; it is already included in total Shield
Block. Max means strongest Hunt augment, not additive copies. Only15NCST labels
change.7existing UI tests, exact15-label audit,20Linux publication/recovery tests,
signature/preflight and all148HTTPS assets verify; no native/DLL/server change.
Source E:/EQ_Local_Dev/_worktrees/character-stats-font,
docs/releases/character-stats-font-20261106/; topic character-stats-font.
''')
    new['items.md']=new['items.md'].replace('signed2026110602/proxy0.13.4','signed2026110603/proxy0.13.4')
    new['items.md']=new['items.md'].replace('Shield Block/Hunt,\nrelative Dodge','Shield Block/Hunt aug block,\nrelative Dodge')
    new['operations.md']=new['operations.md'].replace('Signed0.13.4/2026110602 DLL/catalog/Inventory XML is published; all148assets verify.',
        'Current signed0.13.4/2026110603 is an XML-only font/label correction;147assets\nincluding DLL/catalog retained, all148HTTPS assets verify. No runtime restart;\ncurrent native baseline is unchanged. See character-stats-font release receipts.')
    new['wiki.md']=new['wiki.md'].replace('Current wiki20261106-character-stats-v1 replaces20261106-augment-description-v1.',
        'Current wiki20261106-character-stats-font-v1 replaces20261106-character-stats-v1.\nFont/label and Hunt explanation updated; all owning guides reviewed;505files\npreserved. Current source/receipt worktree E:/EQ_Local_Dev/_worktrees/character-stats-font,\ndocs/releases/character-stats-font-20261106/. Owner reports Stats functioning;\nrevised font pixels remain open, separately from broader gameplay acceptance.')
    new['wiki.md']=new['wiki.md'].replace('2026110602/proxy0.13.4 independently verify','2026110603/proxy0.13.4 independently verify')
    manifest=json.loads(new['sources.json']);revision=source['mergeCommit']['oid']+' plus verified font publication records'
    paths=['tools/client_character_stats_ui.py','tools/tests/test_client_character_stats.py']
    paths+=['docs/releases/character-stats-font-20261106/'+n for n in ('README.md','ui-audit.json','source-merge.json',
           'client-public-verification.json','client-published.json','wiki-publication.json','wiki-impact.json','published-source-overrides.patch')]
    entries=[dict(root=ROOT.as_posix(),path=p,role='Reviewed font-only Stats correction; owner function reported, revised pixels QA open',
        revision=revision,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths]
    manifest['topics']['character-stats-font']=entries;manifest['observed_revisions']['character_stats_font_20261106_published']=revision
    for topic in ('client','items','operations','wiki'):
        manifest['topics'][topic]+=[e for e in entries if e['path'].endswith(('README.md','client-public-verification.json','wiki-publication.json'))]
    new['sources.json']=json.dumps(manifest,indent=2)+'\n'
    patch=''.join(''.join(difflib.unified_diff(old[n].splitlines(True),new[n].splitlines(True),fromfile='a/references/'+n,tofile='b/references/'+n)) for n in new)
    (HERE/'installed-skill-update.patch').write_text(patch,encoding='utf-8',newline='\n')
    for n,text in new.items():(SKILL/n).write_text(text,encoding='utf-8',newline='\n')
    (HERE/'skill-maintenance.json').write_text(json.dumps(dict(status='applied',reviewed_entries=len(entries),revision=revision),indent=2)+'\n')
    print('Verified release recorded; skill updated with owner function report and font QA boundary.')


if __name__=='__main__':main()
