"""Guarded wiki/balance knowledge update; prepare exact patch before installation."""
from pathlib import Path
import argparse
import difflib
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
STAGE=HERE/'knowledge'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def prepare():
    for name in ['wiki-publication.json','wiki-public-verification.json']:
        assert json.loads((HERE/name).read_text())['result']=='PASS'
    STAGE.mkdir(exist_ok=True)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    wiki=(SKILL/'references/wiki.md').read_text(encoding='utf-8')
    balance=(SKILL/'references/balance.md').read_text(encoding='utf-8')
    note='''## Build Lab — October22 published

Current wiki release is `20261022-build-lab-v1` after the interactive handbook.
Source E:/EQ_Local_Dev/_worktrees/wiki-interactive, branch feature/build-lab.
`wiki/build_lab.py`, `assets/build-lab-model.js`, `build-lab.js` and `build-lab.css`
add A/B builds, effective stat inputs, eight pinned spells, Hunt item differences,
resolved actions, mana/cast timelines and exhaustive priority-order search. Saves
use nightcap.build-lab.v1, with validated text import/export. No account, DB/API,
gameplay reload or client pairing. Public files stay on the existing asset allowlist.

This is an experimental Classic50 diagnostic, not a complete native simulator or
automatic legal gear/AA/pet planner. September12 content/original class levels and
October18 landed native controls are dated explicitly; current formulas were
reviewed October22. SD/HA cap750, additive DD, floor(SD/2) ordinary ticks, percentage
healing and direct-only heroic scaling have12captured native value checks. Resolved
abilities bypass scaling. 100ms scheduling/6s global ticks, constant incoming and
resolved melee/pet DPS, expected landed percentage, reserved mana and fixed healing
priority are assumptions. Search tests up to720orders, survival then damage; no
subsets, waiting, AA/gear or global optimality. Do not promote results into live
balance or player acceptance. Model/data provenance: docs/build-lab/.

All22guides/432generated routes assessed; Features/Combat/Equipment/Recent changes,
home path and navigation link the lab. Existing gameplay/catalog/command labels
remain. 26Python pass/9POSIX skips,10model scenario groups, existing Node suites,
real browser320/768/1024/1440 and strict-CSP checks pass. The publisher runs16Linux
recovery tests and rehearses pointer rollback, preserving private services/config.
All466HTTPS hashes/headers and five private denials verify. Evidence:
docs/releases/build-lab-20261022/. Website publication is separate from main or
gameplay promotion. Preserve this source/publication in subsequent whole-site builds.

'''
    first=wiki.index('\n\n')+2
    wiki=wiki[:first]+note+wiki[first:]
    wiki=wiki.replace('Current public release is `20261022-interactive-handbook-v1`, following', 'The handbook shell was introduced in `20261022-interactive-handbook-v1`, following',1)
    begin=wiki.index('Live public URL: https://wiki.nightcapgame.org/. Current verified release is')
    end=wiki.index('`update.py` holds',begin)
    wiki=wiki[:begin]+'''Live public URL: https://wiki.nightcapgame.org/. Current verified release is
`20261022-build-lab-v1`; previous is `20261022-interactive-handbook-v1`.
Current publication/recovery: docs/releases/build-lab-20261022/.
Runbook: docs/ops/nightcap-wiki.md; maintenance: wiki/README.md.
Native player and balance acceptance are separate.

'''+wiki[end:]
    first=balance.index('\n\n')+2
    balance=balance[:first]+'''## Browser Build Lab — October22

The wiki's experimental Build Lab is a separate deterministic diagnostic model,
not the native harness. See wiki.md and docs/build-lab/README.md for its exact
scope: eight pinned spells,12captured landed value controls, explicit effective
stats/resolved abilities,100ms steps/6s global ticks and up to720priority orders.
Full AA/equipment/pet derivation, RNG, resist/AI and global optimality are excluded.
Use `node wiki/test_build_lab.cjs` for arithmetic, resource/timer/horizon/death,
import and search contracts; `wiki/test_build_lab.py` pins source fixtures.
`tools/build_lab_data.py` projects only reviewed public fields and original spell
levels. Never infer access from widened spell columns or refresh hashes without
review. The model is published as20261022-build-lab-v1; no runtime/client change
or fresh native/gameplay acceptance follows. Evidence: docs/releases/build-lab-20261022/.

'''+balance[first:]
    manifest=json.loads((SKILL/'references/sources.json').read_text(encoding='utf-8'))
    wiki_paths={'wiki/build.py','wiki/experience.py','wiki/README.md','wiki/content-review.json','wiki/articles/combat.json','wiki/articles/equipment.json','wiki/articles/features.json','wiki/articles/recent-changes.json','docs/ops/nightcap-wiki.md'}
    wiki_paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'wiki').glob('*build_lab*'))
    wiki_paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'wiki/assets').glob('build-lab*'))
    wiki_paths.update(['wiki/build-lab-data.json','wiki/articles/build-lab.json','wiki/test_build_lab.cjs','docs/build-lab/README.md','docs/build-lab/data-provenance.json'])
    wiki_paths.update('docs/releases/build-lab-20261022/'+p for p in ['README.md','verification.json','wiki-review.json','wiki-publication.json','wiki-public-verification.json'])
    balance_paths={'wiki/assets/build-lab-model.js','wiki/build-lab-data.json','wiki/test_build_lab.cjs','tools/build_lab_data.py','docs/build-lab/README.md','docs/build-lab/data-provenance.json','server-mods/code/zone/effects.cpp','server-mods/code/common/nightcap_spell_scaling.h'}
    for topic,paths in [('wiki',wiki_paths),('balance',balance_paths)]:
        entries=manifest['topics'][topic];entries[:]=[e for e in entries if e['path'] not in paths]
        for path in sorted(paths):
            if not (ROOT/path).is_file():continue
            entries.append({'root':ROOT.as_posix(),'path':path,'role':'Reviewed Build Lab implementation, scope, tests or verified publication','revision':revision+' + reviewed release records','sha256':sha(ROOT/path)})
    manifest['observed_revisions']['build_lab_20261022']=revision
    contents={'wiki.md':wiki,'balance.md':balance,'sources.json':json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'}
    preimages={};patch=[]
    for name,text in contents.items():
        target=SKILL/'references'/name;preimages[name]=sha(target)
        (STAGE/name).write_text(text,encoding='utf-8')
        patch.extend(difflib.unified_diff(target.read_text(encoding='utf-8').splitlines(True),text.splitlines(True),fromfile='a/references/'+name,tofile='b/references/'+name))
    (STAGE/'knowledge.patch').write_text(''.join(patch),encoding='utf-8')
    (STAGE/'preimages.json').write_text(json.dumps(preimages,indent=2)+'\n')
    print('Prepared exact knowledge patch and source fingerprints')


def apply():
    pins=json.loads((STAGE/'preimages.json').read_text())
    for name,digest in pins.items():assert sha(SKILL/'references'/name)==digest,'Concurrent knowledge edit; prepare again'
    for name in pins:(SKILL/'references'/name).write_bytes((STAGE/name).read_bytes())
    (STAGE/'receipt.json').write_text(json.dumps({'result':'APPLIED','files':{name:sha(SKILL/'references'/name) for name in pins}},indent=2)+'\n')
    print('Installed wiki and balance knowledge updated')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    apply() if args.apply else prepare()
