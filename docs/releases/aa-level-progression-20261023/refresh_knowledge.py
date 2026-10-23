"""Refresh reviewed Nightcap knowledge only after verified release/publication."""
from pathlib import Path
import difflib,hashlib,json,subprocess
W=Path(__file__).resolve().parents[3];R=Path(__file__).resolve().parent
K=Path('C:/Users/verre/.codex/worktrees/aa-level-wiki/EQ_Local_Dev')
S=Path('C:/Users/verre/.codex/skills/nightcap-development');out=R/'knowledge';out.mkdir(exist_ok=True)
assert json.loads((R/'open-receipt.json').read_text())['gateway_open']
assert json.loads((R/'client/hosted-verification.json').read_text())['hosted']
assert json.loads((R/'guides-publication.json').read_text())['wiki']['result']=='PASS'
assert json.loads((R/'wiki-public-verification.json').read_text())['result']=='PASS'
assert json.loads((R/'guide-public-verification.json').read_text())['result']=='PASS'
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=W,text=True).strip()
wiki_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=K,text=True).strip()
new={}
p=S/'references/multiclass.md';s=p.read_text(encoding='utf-8');a=s.index('## XP\n');b=s.index('## Normal death EXP loss',a)
old=s[a:b];history=old[old.index('No verified THJ'):old.index('Source: C:/Users/verre/.codex/worktrees/aa-point-cost-40000')]
new['references/multiclass.md']=s[:a]+'''## XP — level-scaled AA deployed October23

Main PR305/00f90e9 and the paired server/client release are verified for live
QA. Normal installed PEQ leveling thresholds and rates remain unchanged. With
AA allocation0%, eligible kills/quests/tasks earn two AA per normal level span;
level1→50 yields about98 AA excluding starters and extra grinding. At100%,
normal XP is held and the same current-level XP span earns20 AA. At50%, it
retains half normal XP and earns11 AA per full input span. Valid0–100 selections
persist through zoning/relog, including a full AA wallet. Native +/- buttons
work from level1 in proxy0.12.0/game2026102301; close the game and use Play.

Production AA:LevelBasedPointsPerLevel=20, AA:PassiveExpPercent=10 and
AA:ExpPerPoint=1000000. The last value is fixed storage units, not a million
normal XP requirement: one passive AA at level1 costs500 normal XP, focused50.
Fixed units preserve existing earned points, purchases and partial AA progress
across levels/relogs. Award crossings use each actual native float32 level span;
at Classic50 use its span indefinitely. Modified normal XP is the common basis
before allocation/capping; AA-only/modern multipliers do not multiply it again.
Gray kills, rez/GM/LDoN/excluded sources do not mint bonus AA. Tiny awards can
truncate; do not promise exact fractional carry in every focus/cap scenario.

Source: C:/Users/verre/.codex/worktrees/aa-point-cost-40000/EQ_Local_Dev,
common/aa_progression.h, zone/exp.cpp, zonedb.cpp and gm_commands/aa_exp.cpp
under server-mods/code. tests/test_level_aa.py, test_level_aa_integration.py and
test_passive_aa.py under tools; exact client tests/aa-allocation-native.cpp.
369award/129legacy/8actual SetEXP/167client checks,112exact executable guards
and27Windows/Linux operator cases pass. Fresh world/zone/shared_memory are
paired for the new rule; all12 zones,39schema/499content and91state-table
checks pass. Signed140-file delivery and wiki/private-guide publication verify.
Native window/wire/quest/persistence/balance acceptance remains owner QA.
Evidence, full matrix and recovery: docs/releases/aa-level-progression-20261023/.
Never restore player snapshots. After percentage support is exposed, old images
that coerce positive allocation to100 are incompatible; recovery needs the new
percentage-capable binaries and an explicitly reviewed policy decision.

'''+history+'\n'+s[b:]
p=S/'references/operations.md';s=p.read_text(encoding='utf-8');a=s.index('## AA million-point release');b=s.index('## THJ custom behavior',a)
new['references/operations.md']=s[:a]+'''## Level-scaled AA — October23 deployed for live QA

Main PR305/00f90e9, fresh world4cabbac9/zone41443afd/shared_memory4123b138 and
signed game2026102301/proxy0.12.0 are paired. One new rule value20 with existing
passive10% gives2 AA per level at0% and20 per level-equivalent at100%, which
holds normal XP. Normal leveling and earned/fractional AA state are preserved.
Evidence: C:/Users/verre/.codex/worktrees/aa-point-cost-40000/EQ_Local_Dev/
docs/releases/aa-level-progression-20261023/. Active stage is
/opt/nightcap/releases/aa-level-progression-20261023-v3; image5e501da8.
Full backup,91saved-state tables, exact1077rule rows,12zone hashes,
39schema/499content checks and one native market rotation verify before reopening.
Client140 hosted files and wiki467/private-guide5 publication verify separately.
Owner native gameplay acceptance remains open. No player snapshot restoration.

Failed v1 guard used gameplay expiry instead of native delayed instance purge:
match expire_at!=0, never_expires=0 and expire_at<=now-offset with active
Instances:ExpireOffsetTimeSeconds3600, projected600seconds ahead. World startup
and450000ms periodic purge share this predicate. Keep all other cleanup guards.
No instance deletion/exception was needed. Byte-exact base64 staging avoids
Windows newline conversion. v2 image passed but disk reserve stopped activation;
v3 reused its exact immutable ID, hashes/layers/dependencies/supervisor checks.
Only11 explicitly approved duplicate uploads and4 cache IDs created by this task
were removed. No installed image, unrelated cache, player data or backup removed.
672MiB prebuilt reserve budgets512runtime+128backup+32publication; actual new
compressed backup65173102bytes. Keep512MiB post-backup/pre-open floor. Future
releases must measure their own needs, not reuse this reserve indiscriminately.

New rules require paired world/zone; runtime child exit restarts everything.
After native percentage controls are exposed, retained older AA images are not
compatible rollback. Follow RECOVERY.md; preserve earned state and stop access
on failed invariants. Retired Goldwind boosts/timed-XP policy remain in effect.

'''+s[b:]
p=S/'references/client.md';s=p.read_text(encoding='utf-8');a=s.index('\n## ')
new['references/client.md']=s[:a]+'''
## Level-1 AA allocation controls — October23 published

Game2026102301 pairs proxy/catalog0.12.0 with level-scaled AA server PR305.
Exactly DLL and patch catalog change;138 unrelated assets, descriptors/history,
Classic robe repair and waypoint models are retained. All140 hosted hashes,
shipped-key signature and actual DLL/catalog pairing verify. Close the game and
use normal launcher Play. Protected reference client remains read-only.

src/ui_hooks.h and tests/aa-allocation-native.cpp under eq-client-dll guard three
native level gates and native +/- bounds for non-ten allocations1–9/91–99,
then delegate native Notify. No global level spoofing or AA purchase changes.
Canonical patch-sites.json and generated contracts must stay paired. Native167
control checks,10runtime groups and112exact executable guards pass. Wire,
rendered controls, real rewards and owner acceptance remain in-game QA.
Source/evidence: C:/Users/verre/.codex/worktrees/aa-point-cost-40000/EQ_Local_Dev/
docs/releases/aa-level-progression-20261023/client/ and ../QA.md. Never revert
only one half of the proxy/catalog or expose the old0/100-only server afterward.
'''+s[a:]
new['references/client.md']=new['references/client.md'].replace('Keep current proxy/catalog0.11.1 and Classic','That historical release retained proxy/catalog0.11.1 and Classic')
p=S/'references/wiki.md';s=p.read_text(encoding='utf-8');a=s.index('\n## ')
new['references/wiki.md']=s[:a]+'''
## Level-scaled AA guidance — October23 published

Current wiki20261023-aa-level-v1 preserves the loot finder, automatic JSON
reader/timer, Build Lab and interactive handbook. Source is
C:/Users/verre/.codex/worktrees/aa-level-wiki/EQ_Local_Dev, feature/aa-level-wiki;
never publish the older gameplay checkout's wiki. Six guides, Features/home,
commands and Recent changes explain2passive AA/level,98by50, native level1
0–100controls,50%=half level+11AA and100%=held level+20AA per input span.
Crossing awards use each span. Existing progress and Goldwind retirement remain.
Normal leveling is unchanged; owner native gameplay acceptance remains open.

Whole-wiki23guides/432generated routes/384Hunt variants reviewed. Build Lab
initializes only #build-lab[data-lab], avoiding the existing Recent changes
heading with the same ID; narrow selector fix retains anchors. Its source pin
was reviewed for the AA-only rule-header addition; spell formulas unchanged.
All467 HTTPS files/security headers and5private denials verify, plus private
player-guide20261023-aa-level-guide-v1/all5files. Publisher checks both expected
pointers and private baseline hashes under one website lock;6concurrency/remote
syntax regressions pass. No Nginx configuration/service identity change.
67Linux wiki cases, Node suites and21responsive browser layouts passed.
Evidence: gameplay checkout docs/releases/aa-level-progression-20261023/.
'''+s[a:]
# Update only source paths reviewed for this change; retain unrelated dated inputs.
p=S/'references/sources.json';d=json.loads(p.read_text(encoding='utf-8'))
rbase='docs/releases/aa-level-progression-20261023/'
paths={
'multiclass':['server-mods/code/common/aa_progression.h','server-mods/code/common/ruletypes.h','server-mods/code/zone/exp.cpp','server-mods/code/zone/client.h','server-mods/code/zone/client.cpp','server-mods/code/zone/zonedb.cpp','server-mods/code/zone/gm_commands/aa_exp.cpp','tools/tests/test_level_aa.py','tools/tests/test_level_aa_integration.py','tools/tests/test_passive_aa.py',rbase+'README.md',rbase+'matrix.md',rbase+'open-receipt.json'],
'client':['eq-client-dll/src/ui_hooks.h','eq-client-dll/config/patch-sites.json','eq-client-dll/tests/aa-allocation-native.cpp',rbase+'client/hosted-verification.json',rbase+'client/publish.py',rbase+'client/test_publish.py'],
'operations':[rbase+n for n in ['rollout.py','test_rollout.py','native-build-manifest.json','preflight-receipt.json','open-receipt.json','RECOVERY.md','instance-expiry-audit.json','preflight-recovery.json']],
'wiki':[rbase+n for n in ['wiki-review.json','publish_guides.py','test_publish_guides.py','guides-publication.json','wiki-public-verification.json','guide-public-verification.json']]
}
for topic,names in paths.items():
 d['topics'][topic]=[e for e in d['topics'][topic] if e['path'] not in names]
 for n in names:
  d['topics'][topic].append({'root':W.as_posix(),'path':n,'revision':revision+'; reviewed deployed October23 release','sha256':hashlib.sha256((W/n).read_bytes()).hexdigest(),'role':'Reviewed level-scaled AA implementation/verification; native owner acceptance remains open'})
wiki_paths=['wiki/articles/'+n+'.json' for n in ('commands','features','getting-started','index','multiclass','recent-changes')]+['wiki/assets/build-lab.js','wiki/test_wiki.py','wiki/content-review.json','wiki/README.md','docs/build-lab/data-provenance.json']
d['topics']['wiki']=[e for e in d['topics']['wiki'] if e['path'] not in wiki_paths]
for n in wiki_paths:d['topics']['wiki'].append({'root':K.as_posix(),'path':n,'revision':wiki_revision+'; reviewed published AA guidance','sha256':hashlib.sha256((K/n).read_bytes()).hexdigest(),'role':'Current published AA guidance preserving loot finder/Build Lab; native owner QA separate'})
d['observed_revisions']['aa_level_progression_20261023']='main00f90e9; deployed image5e501da8; client2026102301; wiki20261023-aa-level-v1; owner QA open'
new['references/sources.json']=json.dumps(d,indent=2,ensure_ascii=False)+'\n'
patch=[]
for n,value in new.items():
 previous=(S/n).read_text(encoding='utf-8');patch.extend(difflib.unified_diff(previous.splitlines(True),value.splitlines(True),fromfile='a/'+n,tofile='b/'+n));target=out/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(value,encoding='utf-8')
(out/'installed-skill.patch').write_text(''.join(patch),encoding='utf-8')
for n,value in new.items():(S/n).write_text(value,encoding='utf-8')
(out/'receipt.json').write_text(json.dumps({'updated':list(new),'revision':revision,'wiki_revision':wiki_revision,'owner_gameplay_accepted':False},indent=2)+'\n',encoding='utf-8')
print('Updated four relevant references and reviewed source fingerprints; exact patch retained.')
