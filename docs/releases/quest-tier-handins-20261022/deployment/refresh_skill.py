"""Refresh only reviewed quest-tier knowledge, preserving concurrent releases."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SKILL = Path('C:/Users/verre/.codex/skills/nightcap-development')
RELEASE = 'docs/releases/quest-tier-handins-20261022/'


def section(text, old_title, title, body):
    marker='## '+old_title+'\n'
    if marker not in text and '## '+title+'\n' in text: marker='## '+title+'\n'
    if marker in text:
        start=text.index(marker); end=text.find('\n## ',start+len(marker))
        if end < 0: end=len(text)
        return text[:start]+'## '+title+'\n\n'+body.strip()+'\n'+text[end:]
    first=text.index('\n')+1
    return text[:first]+'\n## '+title+'\n\n'+body.strip()+'\n'+text[first:]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    evidence=json.loads((HERE/'live-verification.json').read_text(encoding='utf-8'))
    wiki=json.loads((HERE/'wiki-public-verification.json').read_text(encoding='utf-8'))
    assert evidence['gateway_open'] and wiki['result']=='PASS'
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    body=f'''Owner-authorized main PR290/c66df0e and the paired zone/seven-quest deployment
are verified in {RELEASE}deployment/. Source: {ROOT.as_posix()}.
Normal requirements accept exact generated Polished/Exalted/Ascended family
definitions (+200000/+400000/+600000) in shared Lua/native hand-ins and task
Deliver. Explicit tier requirements stay exact; epic/hunt/dungeon identities and
forging costs remain separate. Exact inputs are preferred; explicit qualities
reserve first. Failure restores tentative counts and actual item instances.
Inherited multiquest completion still clears the whole donation bucket, including
surplus; Lua retains separate trade-slot semantics.

Shakrn14075 in southkarana accepts Aviak Charm13737/213737/413737/613737 plus two
Star Rubies10032, granting the already-live Ascended Crafted Gauntlets604178.
Five soltemple scripts now share native matching for17 recipes. Kurron retains
three Darkforge pieces/raw900pp, faction and one letter/spawn; all64 ordinary
quality combinations pass. Declare submitted currency to CheckHandin, refund
once on success, use native returns on failure. Active root plugins/ differs
from unused captured quests/plugins/ fixtures; do not conflate their evidence.

Zone6da991b6 is the successor to byte-reproduced5dd5a655. Full supervised restart,
fresh stopped backup, all12 zone hashes and exact player/custom/content/cache/
client preservation verified before access reopened. Seven files only; the ten
already-live armor reward scripts remain unchanged. No SQL migration, world,
cache ABI or client update. Never kill one zone or restore player snapshots.
Windows/Linux native method tests, actual Lua callbacks,357 Perl assertions,
113 armor Lua cases,21 catalog guards and16 deployment fault tests pass.
Owner gameplay acceptance and complete task-delivery lifecycle QA remain open;
exact source/tests/build/rollback boundary and QA: {RELEASE}.
'''
    wiki_body=f'''Main PR290 and paired runtime/quest activation are verified. All21 guides and
432 generated routes reviewed; six ingredient notices and search now say Live
testing. Wiki20261022-quest-tiers-v1 verifies465 HTTPS hashes/security headers and
five private-route denials. Current class-armor rewards, robes2203, waypoints,
384catalog values and commands are preserved. No client update. Native owner
QA remains open. Source: {ROOT.as_posix()}; evidence: {RELEASE}deployment/.
'''
    updates={}
    for name in ['world','items','wiki','operations']:
        p=SKILL/'references'/(name+'.md');old=p.read_text(encoding='utf-8')
        new=section(old,'Quest ingredient qualities — October 22 candidate',
                    'Quest ingredient qualities — October22 deployed for live QA',wiki_body if name=='wiki' else body)
        if name=='items':
            new=new.replace('The current live release does not include the broader native ingredient-quality\nor currency correction below.',
                            'The later quest-tier PR290 deployment installs the native ingredient-quality\nand currency correction described above.')
            start=new.find('Separate successor candidate: E:/EQ_Local_Dev/_worktrees/quest-tier-handins')
            if start>=0:
                end=new.find('\n## ',start)
                new=new[:start]+('Successor PR290 is deployed: paired zone and seven files, including the corrected\nKurron. Ten live armor reward scripts are preserved; current quest-tier evidence\nis linked above. Native fresh-hand-in and balance acceptance remain open.\n')+new[end:]
        if name=='wiki':
            new=new.replace('Broader ingredient-tier/native currency work is\na separate unpublished candidate; no global quest/craft quality guarantee.',
                            'The later quest-tier PR290 deployment and wiki20261022-quest-tiers-v1\nadd ordinary ingredient matching and the native currency correction. Explicit\ntier requirements and crafting recipes remain separate; owner QA stays open.')
        updates[p]=(old,new)
    p=SKILL/'references/sources.json';old=p.read_text(encoding='utf-8');sources=json.loads(old)
    old_scope=json.loads((ROOT/RELEASE/'skill-update/scoped-fingerprints.json').read_text(encoding='utf-8'))
    paths={topic:[e['path'] for e in entries] for topic,entries in old_scope['topics'].items()}
    paths['operations']=[RELEASE+'deployment/'+n for n in ['rollout.py','test_rollout.py','manifest.json','live-verification.json','README.md','review.json']]
    paths['wiki'] += [RELEASE+'deployment/'+n for n in ['wiki-review.json','wiki-publication.json','wiki-public-verification.json']]
    scoped={'schema_version':sources['schema_version'],'audited_at':'2026-10-22','topics':{}}
    for topic,names in paths.items():
        entries=[{'root':ROOT.as_posix(),'path':n,'revision':revision,
                  'role':'quest ingredient release deployed; owner gameplay QA pending',
                  'sha256':hashlib.sha256((ROOT/n).read_bytes()).hexdigest()} for n in names]
        sources['topics'][topic]=[e for e in sources['topics'][topic]
            if not(e['root']==ROOT.as_posix() and e['path'] in names)]+entries
        scoped['topics'][topic]=entries
    # Only these armor integration files were changed and reviewed here.
    reviewed_armor={'server-mods/quests/overthere/Kurron_Ni.pl','docs/items/quest-armor-catalog.json',
                    'docs/releases/quest-armor-20261022/README.md'}
    for entries in sources['topics'].values():
        for e in entries:
            if e['root'].endswith('/quest-armor-ascended') and e['path'] in reviewed_armor:
                e.update(root=ROOT.as_posix(),revision=revision,
                         sha256=hashlib.sha256((ROOT/e['path']).read_bytes()).hexdigest(),
                         role='reviewed deployed armor/ingredient integration; QA pending')
    sources['observed_revisions']['quest_tier_handins_20261022']=revision
    updates[p]=(old,json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
    out=HERE/'skill-update';out.mkdir(exist_ok=True)
    patch=''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=p.as_posix(),tofile=p.as_posix())) for p,(a,b) in updates.items())
    (out/'knowledge.patch').write_text(patch,encoding='utf-8',newline='\n')
    (out/'scoped-fingerprints.json').write_text(json.dumps(scoped,indent=2)+'\n',encoding='utf-8')
    if args.apply:
        for p,(a,b) in updates.items():
            assert p.read_text(encoding='utf-8')==a,'Concurrent knowledge update; reprepare'
        for p,(a,b) in updates.items():p.write_text(b,encoding='utf-8',newline='\n')
    (out/'receipt.json').write_text(json.dumps({'status':'installed' if args.apply else 'prepared','revision':revision,
        'files':{p.as_posix():hashlib.sha256(b.encode()).hexdigest() for p,(a,b) in updates.items()}},indent=2)+'\n',encoding='utf-8')
    print('Installed' if args.apply else 'Prepared',len(updates),'knowledge files')


if __name__=='__main__':main()
