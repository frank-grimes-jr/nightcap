"""Record verified title-preview publication in installed Nightcap knowledge."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'docs/titles/wiki-release'
ART=ROOT/'artifacts/titles-wiki-20261112'
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    proof=json.loads((HERE/'publication.json').read_text(encoding='utf-8'))
    public=json.loads((HERE/'public-verification.json').read_text(encoding='utf-8'))
    assert proof['result']=='PASS' and public['status']=='PASS'
    assert proof['files']==public['files']==614 and proof['preserved_files']==600
    assert proof['rollback_rehearsed'] and public['all_public_sha256_and_security_headers']
    changes=[]

    def change(name,text):
        changes.append(dict(path=name,before_sha256=sha(SKILL/name),after=text))

    ref=(SKILL/'references/titles.md').read_text(encoding='utf-8')
    start=ref.index('Native title selection')
    prefix='''# Earned titles — main source and published wiki preview

Main PR428/f689f7aa contains77cosmetic titles. The owner separately requested
“Push to wiki” on November12. Wiki20261112-earned-titles-v1 is now published at
https://wiki.nightcapgame.org/titles.html with all614HTTPS hashes/headers and five
private404denials verified. It adds one page/13changed outputs and retains600exact
files after reproducing the authenticated613-file DoT v2 source. The preview is
Not released: title runtime is not activated and normal-player QA remains OPEN.
Twenty site/refresh tests, exact77-title/search/equipment/experience controls and
16Linux publisher tests pass. Pointer rollback was rehearsed; five service IDs/
start times, config bytes/inode, channel and private downloads remain unchanged.
No Nginx reload, client update, game restart or title gameplay acceptance.

Source/evidence: E:/EQ_Local_Dev/_worktrees/earned-titles; topic `titles`.
docs/titles/wiki-release/README.md owns the exact public source, receipts and
one-shot recovery boundary. Reproduce the current public source for later
publication; never republish a stale main mirror or replay the terminal updater.

'''
    ref=prefix+ref[start:]
    markers=['Contract, exact player QA, activation/recovery','Contract and exact player QA:']
    at=next(ref.index(marker) for marker in markers if marker in ref)
    ref=ref[:at]+'''Contract and exact player QA: docs/titles/{SPEC,QA,README}.md. Published Titles,
Features/Home, commands/previews/Change Log and five owning guides retain
Not released labels. Browser rendering/RoF2 picker/nameplate acceptance remain
unverified. Global historical wiki drift stays REVIEW REQUIRED; no ledger advance.
'''
    change('references/titles.md',ref)
    wiki=(SKILL/'references/wiki.md').read_text(encoding='utf-8')
    wiki=wiki.replace('The later main earned-titles candidate (PR428/f689f7aa) stays disabled and\nunpublished. Its extra authoring guide and Home/Features/command context are\npreserved in the repository; the verified613-file DoT artifact excludes that\npreview. concurrent-source-review.json records the explicit source/public scope.',
        'The retained613-file DoT artifact excluded the then-unpublished title preview.\nThe subsequent titles release below adds that preview separately while leaving\ntitle gameplay disabled. concurrent-source-review.json retains the earlier scope.')
    replacement='''## Earned titles — November12 wiki preview published

Owner requested “Push to wiki” after main PR428/f689f7aa. Release20261112-earned-
titles-v1 reproduces all613DoT v2 outputs before one added title page/13changed
outputs, preserving600files. All43authored guides and generated item/zone/catalog
impacts assessed; no item/reward values, acquisitions or client behavior changes.
Titles/Home/Features/commands/owning guides and Change Log keep Not released.
Runtime is not activated; publication is not normal-player gameplay acceptance.

Twenty site/refresh tests and exact77-title/real-search/equipment/experience
controls pass.16Linux publisher checks and all614HTTPS hashes/security headers
plus five private404denials verify. Pointer rollback rehearsed; five service IDs/
start times, config bytes/inode, channel/private downloads preserved. No Nginx
reload/game restart. Browser rendering remains unverified. Historical REVIEW
REQUIRED stays; no blanket ledger advance. Source/evidence/recovery:
E:/EQ_Local_Dev/_worktrees/earned-titles/docs/titles/wiki-release/; context `titles`.
Never replay a terminal publication or overwrite a later relative pointer.
'''
    wiki,count=re.subn(r'## Earned titles[^\n]*\n.*?(?=\n## |\Z)',lambda m:replacement,wiki,flags=re.S)
    assert count==1
    change('references/wiki.md',wiki)
    manifest=json.loads((SKILL/'references/sources.json').read_text(encoding='utf-8'))
    for entry in manifest['topics']['titles']:
        actual=sha(ROOT/entry['path'])
        if actual!=entry['sha256']:
            assert entry['path'] in ['docs/titles/README.md','docs/titles/wiki-impact.md',
                                     'tools/update_titles_wiki_knowledge.py'],entry['path']
            entry['sha256']=actual
    new={
        'tools/prepare_titles_wiki.py':'Authenticated613-output reproduction and scoped preview-only changes',
        'tools/check_titles_wiki.py':'Exact77requirements, preview labels and real search/neighbor controls',
        'tools/publish_titles_wiki.py':'Owner-authorized guarded pointer update with preserved services/config/channel/downloads',
        'tools/verify_titles_wiki.py':'614public HTTPS hashes/headers and private denials',
        'tools/update_titles_wiki_knowledge.py':'Preimage-checked publication knowledge maintenance',
        'docs/titles/wiki-release/README.md':'Published guide, exact source and terminal recovery boundary',
        'docs/ops/nightcap-wiki.md':'Current614-file publication authority with earlier hosting snapshots explicitly retained',
        'docs/titles/wiki-release/source-reproduction.json':'Fresh authenticated public baseline reproduction',
        'docs/titles/wiki-release/candidate.json':'43-guide review, exact scope and600retained files',
        'docs/titles/wiki-release/content-checks.json':'77exact title requirements and browser-search controls',
        'docs/titles/wiki-release/publication.json':'Verified pointer rollback and preserved private/service state',
        'docs/titles/wiki-release/public-verification.json':'All614HTTPS hashes/headers and five private404denials',
    }
    for name,role in new.items():
        rows=manifest['topics']['titles']
        rows[:]=[e for e in rows if not(e['root']==ROOT.as_posix() and e['path']==name)]
        rows.append(dict(root=ROOT.as_posix(),path=name,role=role,sha256=sha(ROOT/name)))
    manifest['observed_revisions']['earned_titles_wiki_20261112']='20261112-earned-titles-v1 published from authenticated DoT v2 source;614HTTPS files verified. MainPR428/f689f7aa; title runtime disabled and player QA OPEN.'
    change('references/sources.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    patch=''
    for item in changes:
        before=(SKILL/item['path']).read_text(encoding='utf-8')
        patch+=''.join(difflib.unified_diff(before.splitlines(True),item['after'].splitlines(True),
                    fromfile='a/'+item['path'],tofile='b/'+item['path'],n=0))
    (HERE/'installed-skill.patch').write_text(patch,encoding='utf-8',newline='\n')
    (ART/'skill-plan.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Prepared verified publication knowledge patch')


def apply():
    changes=json.loads((ART/'skill-plan.json').read_text(encoding='utf-8'))
    for item in changes:
        assert sha(SKILL/item['path'])==item['before_sha256'],item['path']+' changed; re-review before applying'
    for item in changes:
        (SKILL/item['path']).write_text(item['after'],encoding='utf-8',newline='\n')
    print('Installed verified title preview publication knowledge; runtime remains disabled')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    args=parser.parse_args();apply() if args.apply else prepare()
