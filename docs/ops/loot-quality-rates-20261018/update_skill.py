"""Prepare a narrow, current-preimage skill patch; --apply installs that patch."""
import argparse
import difflib
import hashlib
import json
import subprocess
from pathlib import Path

args=argparse.ArgumentParser()
args.add_argument('--apply',action='store_true')
options=args.parse_args()
root=Path(__file__).resolve().parents[3]
skill=Path('C:/Users/verre/.codex/skills/nightcap-development/references')
evidence=Path(__file__).resolve().parent
result=evidence/'result.json'
live=result.exists() and bool(result.stat().st_size) and json.loads(result.read_text(encoding='utf-8'))['status']=='activated_verified'
state='deployed and globally reloaded; player balance QA remains open' if live else 'tested and prepared; activation awaits the concurrent production deployment'
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
updates={}
p=skill/'items.md';old=p.read_text(encoding='utf-8')
heading='## Ordinary loot rates and quest reward direction — October 18\n'
section=(heading+'\n20% Polished / 5% Exalted / 1% Ascended: '+state+'.\n'
 'Existing Zone:LootTierRare/Epic/LegendaryChance DB overrides are 2000/500/100\n'
 'out of10000 when activated; compiled defaults remain1000/200/25. One roll per\n'
 'eligible ordinary equipment/bag drop, not kill. Missing variants stay base;\n'
 'hunt/dungeon rates and3/4/4 reforging are separate. Existing generated loot is\n'
 'not rerolled. No binary/cache/client change; world and all zones reload rules.\n\n'
 'Actual deployed source is server-mods/code/zone/loot.cpp, matching the retained\n'
 'October17 and October18 cooldown manifests. The older loottables.cpp pointer\n'
 'does not describe this reviewed build. Exhaustive native roll test and five\n'
 'temporary MariaDB guard/forward/inverse cases pass. Evidence/operator/QA:\n'
 'E:/EQ_Local_Dev/_worktrees/loot-quality-rates/docs/ops/loot-quality-rates-20261018/.\n\n'
 'Owner wants automatic Ascended quest armor/weapons excluding repeatable/easily\n'
 'farmed quests. This is design-only, not implemented. Require an audited final-\n'
 'reward catalog; do not hook all SummonItem/QuestReward calls (returns and\n'
 'components share them). Many Classic hand-ins are repeatable and excluded.\n'
 'Preserve separate epic+800000 progression; ordinary variants use+600000.\n'
 'See quest-reward-policy.md for local examples and required production audit.\n\n')
if heading in old:
    start=old.index(heading);end=old.find('\n## ',start+len(heading))
    new=old[:start]+section+(old[end+1:] if end!=-1 else '')
else:
    index=old.index('\n')+1;new=old[:index]+'\n'+section+old[index:].lstrip('\n')
lines=new.splitlines()
for i,line in enumerate(lines):
    if line.startswith('| Legacy quality loot |'):
        lines[i]='| Legacy quality loot | Base/Polished/Exalted/Ascended, offsets +200k/+400k/+600k; epics separate +800k. October18 rates20%/5%/1%; see activation status above. Per eligible drop, not kill. | `server-mods/code/zone/loot.cpp`, exact retained manifests and `docs/ops/loot-quality-rates-20261018/` |'
new='\n'.join(lines)+'\n';updates[p]=(old,new)
p=skill/'wiki.md';old=p.read_text(encoding='utf-8')
old_heading='## October18 ordinary loot tuning — local notices pending publication\n'
heading='## October18 ordinary loot tuning — publication status\n'
old=old.replace(old_heading,heading)
section=(heading+'\nThe loot-quality-rates checkout maintains Equipment, Features, home, Recent\n'
 'changes and Unreleased notices for approved20%/5%/1% ordinary loot tuning.\n'
 'Activation status is in docs/ops/loot-quality-rates-20261018/README.md.\n'
 'Quest auto-Ascended is design-only, excluding repeatable/easily farmed quests.\n'
 'All21 guides and432 generated reward routes have an impact assessment; hunt\n'
 'catalog values and commands remain unchanged. Fourteen content/refresh tests\n'
 'pass;16 Linux publisher/recovery checks also pass. Release20261018-loot-quality-v1\n'
 'publishes the live rates over20261018-reforge-colors-v1, preserving current\n'
 'main137def1 travel/cooldown/reforging guidance. See wiki-publication.json and\n'
 'wiki-public-verification.json for origin/public evidence; gameplay balance QA\n'
 'remains open. Whole-wiki decisions: wiki-review.json.\n\n')
if heading in old:
    start=old.index(heading);end=old.find('\n## ',start+len(heading))
    new=old[:start]+section+(old[end+1:] if end!=-1 else '')
else:
    index=old.index('\n')+1;new=old[:index]+'\n'+section+old[index:].lstrip('\n')
updates[p]=(p.read_text(encoding='utf-8'),new)
p=skill/'sources.json';old=p.read_text(encoding='utf-8');manifest=json.loads(old)
entries={
 'server-mods/code/zone/loot.cpp':'actual retained-build ordinary tier-roll hook',
 'server-mods/code/common/ruletypes.h':'historical compiled defaults; live tuning uses existing DB overrides',
 'tools/tests/test_loot_quality_rates.py':'exhaustive actual native loot-block verification',
 'docs/ops/loot-quality-rates-20261018/README.md':'October18 loot tuning activation, rollback and QA boundary',
 'docs/ops/loot-quality-rates-20261018/ops/apply.py':'guarded three-rule transaction and global reload operator',
 'docs/ops/loot-quality-rates-20261018/quest-reward-policy.md':'accepted exclusions; quest automatic top-tier remains design-only',
}
if live:entries['docs/ops/loot-quality-rates-20261018/result.json']='verified live rule activation receipt; player QA distinct'
topic=manifest['topics']['items']
topic[:]=[row for row in topic if row['path'] not in entries]
for path,role in entries.items():
    topic.append({'root':root.as_posix(),'path':path,'role':role,'revision':revision+' + reviewed working evidence','sha256':hashlib.sha256((root/path).read_bytes()).hexdigest()})
manifest['observed_revisions']['loot_quality_20261018']=revision
path='docs/ops/loot-quality-rates-20261018/wiki-review.json'
topic=manifest['topics']['wiki']
topic[:]=[row for row in topic if row['path']!=path]
topic.append({'root':root.as_posix(),'path':path,'role':'whole-wiki impact review; live loot notices published and verified',
              'revision':revision+' + reviewed working evidence','sha256':hashlib.sha256((root/path).read_bytes()).hexdigest()})
updates[p]=(old,json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
patch=''.join(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=p.as_posix(),tofile=p.as_posix())) for p,(old,new) in updates.items())
(evidence/'installed-skill.patch').write_text(patch,encoding='utf-8')
if options.apply:
    for p,(old,new) in updates.items():
        assert p.read_text(encoding='utf-8')==old, 'Concurrent skill edit; regenerate patch'
    for p,(_,new) in updates.items():p.write_text(new,encoding='utf-8')
    print('Installed narrow items reference and reviewed fingerprint updates')
else:print('Exact installed-skill.patch saved; not installed')
