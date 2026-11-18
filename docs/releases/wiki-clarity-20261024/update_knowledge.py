"""Prepare/apply the owner's required wiki knowledge update with exact preimages."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
STAGE=Path('E:/EQ_Local_Dev/artifacts/wiki-clarity-20261024/knowledge')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def prepare():
    for name in ['wiki-publication-v2.json','wiki-public-verification.json']:
        assert json.loads((HERE/name).read_text())['result']=='PASS'
    STAGE.mkdir(parents=True,exist_ok=True)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    wiki=(SKILL/'references/wiki.md').read_text(encoding='utf-8')
    note='''## Clear Features, Guides and Change Log — October24 published

Current release is20261024-wiki-clarity-v2, following clarity-v1 and the Hole wiki.
Source E:/EQ_Local_Dev/_worktrees/wiki-clarity, feature/wiki-clarity. Features is
eight defining departures from standard EQ; Guides owns current instructions;
Change Log (existing recent-changes.html URL) owns dated releases, minor changes
and fixes. Do not prepend announcements to Home/Features or repeat them across
guides. Update the current instruction in its owning guide and log the date once.

`wiki/assets/clarity.css` owns the shared type scale, compact navigation/contents,
guide disclosures and archived-update targets. `experience.py` keeps four compact
home paths without the old release digest. `build.py` lists maintained guides,
with item/zone directories separate, and supplies Home/Features/Guides/Change Log
tabs. Current model/tool/reader/catalog behavior is preserved. Native details
disclosures and old article anchors remain usable; `experience.js` opens both the
target disclosure and its ancestors. Archived notice targets display a contextual
Change Log link only when requested. Search aliases lead AA/classes to Multiclass
and fixes to Change Log. One-time migration: tools/wiki_clarity_migration.py.

All24maintained guides/447generated reward routes reviewed against the published
66c7b843 baseline, retaining Chapterhouse, AA progression, the keyless Hole and
candidate/QA boundaries. The High Keep rescue candidate remains unpublished and
must reconcile this new editorial source before a whole-site publication.
70local Python cases:43pass/27POSIX-only skips;16Linux publisher/recovery cases
pass. Existing Node tool/search suites and new old-anchor/disclosure regressions
pass.32real browser layouts at320/768/1024/1440, old links, goal navigation,
quick search and light/dark reading verify. All483HTTPS hashes/security headers
and five private-route denials pass. Pointer rollback/private downloads/service
identities/config are preserved. No gameplay reload, client pairing or native
balance acceptance is implied. Evidence: docs/releases/wiki-clarity-20261024/.

'''
    pos=wiki.index('\n\n')+2;wiki=wiki[:pos]+note+wiki[pos:]
    wiki=wiki.replace('production remains20261024-hole-keyless-v1.','the latest public wiki is20261024-wiki-clarity-v2; reconcile its editorial structure before publication.',1)
    begin=wiki.index('Live public URL: https://wiki.nightcapgame.org/.')
    end=wiki.index('`update.py` holds',begin)
    wiki=wiki[:begin]+'''Live public URL: https://wiki.nightcapgame.org/. Current verified release is
20261024-wiki-clarity-v2 from E:/EQ_Local_Dev/_worktrees/wiki-clarity.
Its publication, complete HTTPS verification and recovery evidence are in
docs/releases/wiki-clarity-20261024/. Preserve Features/Guides/Change Log boundaries,
existing tools and candidate labels in future updates. Native player and balance
acceptance remain separately recorded. Maintenance: wiki/README.md.

'''+wiki[end:]
    wiki=wiki.replace('Features uses grouped reading rows in `articles/features.json` and wiki.css.','Features uses eight curated reading rows in `articles/features.json`; `clarity.css` supplies the shared hierarchy. Change Log owns release notices and fixes; current instructions stay in Guides.')
    manifest=json.loads((SKILL/'references/sources.json').read_text(encoding='utf-8'))
    paths={'wiki/build.py','wiki/experience.py','wiki/README.md','wiki/content-review.json','wiki/assets/clarity.css','wiki/assets/experience.js','wiki/assets/search.js','wiki/test_wiki.py','wiki/test_experience.cjs','wiki/test_search.cjs','tools/wiki_clarity_migration.py','docs/ops/nightcap-wiki.md'}
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'wiki/articles').glob('*.json'))
    paths.update('docs/releases/wiki-clarity-20261024/'+name for name in ['README.md','content-review.json','verification.json','wiki-publication-v2.json','wiki-public-verification.json'])
    entries=manifest['topics']['wiki']
    entries[:]=[e for e in entries if e['path'] not in paths or 'highkeep-rescue-wiki' in e['root']]
    for path in sorted(paths):
        entries.append({'root':ROOT.as_posix(),'path':path,'role':'Reviewed current wiki editorial structure, content or verified publication','revision':revision,'sha256':sha(ROOT/path)})
    manifest['observed_revisions']['wiki_clarity_20261024']=revision
    texts={'wiki.md':wiki,'sources.json':json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'}
    pins={};patch=[]
    for name,text in texts.items():
        target=SKILL/'references'/name;pins[name]=sha(target)
        (STAGE/name).write_text(text,encoding='utf-8')
        patch.extend(difflib.unified_diff(target.read_text(encoding='utf-8').splitlines(True),text.splitlines(True),fromfile='a/references/'+name,tofile='b/references/'+name))
    (STAGE/'knowledge.patch').write_text(''.join(patch),encoding='utf-8')
    (STAGE/'preimages.json').write_text(json.dumps(pins,indent=2)+'\n')
    print('Prepared exact current wiki knowledge patch and reviewed source pins')


def apply():
    pins=json.loads((STAGE/'preimages.json').read_text())
    for name,digest in pins.items():assert sha(SKILL/'references'/name)==digest,'Concurrent skill edit; prepare and review again'
    for name in pins:(SKILL/'references'/name).write_bytes((STAGE/name).read_bytes())
    report={'result':'APPLIED','files':{name:sha(SKILL/'references'/name) for name in pins}}
    (STAGE/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true')
    apply() if parser.parse_args().apply else prepare()
