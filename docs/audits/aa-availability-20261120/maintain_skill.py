from pathlib import Path
import difflib,hashlib,json,subprocess
A=Path(__file__).resolve().parent
W=Path('E:/EQ_Local_Dev/_worktrees/aa-availability')
K=Path('C:/Users/verre/.codex/skills/nightcap-development')
D=W/'docs/audits/aa-availability-20261120'
dep=json.loads((D/'production-verified.json').read_bytes())
assert dep['gateway_open'] and dep['workers']==12
assert json.loads((D/'wiki-public-verification.json').read_bytes())['result']=='PASS'
rev=subprocess.check_output(['git','rev-parse','origin/main'],cwd=W,text=True).strip()
changes={}
section='''## AA availability — November 20 deployed

All 489 allowed families / 1,845 ranks remain unchanged. The current live AA tables exactly matched the policy fixture at audit. Fury of Magic215 (nine ranks) and Mystical Attuning334 (three) already exist. Worksheet aliases and intentional exclusions are recorded; do not treat different THJ rank counts as missing access.

Mastery of the Past150 now waives only Spell Casting Expertise26 when the player holds CLR/PAL/RNG/DRU/SHM/BST. The enabled union line had inherited a prerequisite those classes cannot buy; disabled equivalent251 has their original no-prerequisite path. SHD/BRD/NEC/WIZ/MAG/ENC-only builds retain Expertise III. common/aa_availability.h serves both native purchase and per-client AA packet filtering; shared rank definitions stay intact. No ranks, prices, effects, masks, SQL, custom content or client assets change. Existing earned projection/refunds remain; already-earned eligible ranks survive prerequisite changes.

Evidence: E:/EQ_Local_Dev/_worktrees/aa-availability/docs/audits/aa-availability-20261120/. All696 single/pair/trio class sets audited. Native extracted purchase5808 and packet5724 cases pass, 65536mask controls, 30focused/adjacent tests and11dev checks pass. Shipping predecessor35330918 was reproduced exactly before full aa.cpp compilation. These fixtures are not real SQL purchase/release or visible-client acceptance; that QA stays OPEN. Whole-runtime zone release and12workers verified; relog for AA-window refresh. No cache rebuild or client download. Current generator passes; an older all-class generation test is stale on unchanged main and remains separately documented.

'''
p=K/'references/multiclass.md';old=p.read_text(encoding='utf-8');new=old.replace('# Multiclass, spells, skills and advancement\n\n','# Multiclass, spells, skills and advancement\n\n'+section,1)
new=new.replace('The deployed\n26-line expansion now allows394 families/1,051 ranks','The historical October13\n26-line expansion allowed394 families/1,051 ranks',1)
assert new!=old;changes[p]=(old,new)
p=K/'references/operations.md';old=p.read_text(encoding='utf-8');new=old.replace('## Current native production baseline · fast direct healing November20','## Previous native production baseline · fast direct healing November20',1)
entry='## Current native production baseline · AA availability November20\n\nStage aa-availability-20261120-v1, source'+dep['source']+', zone'+dep['binaries']['zone']+'. The exact fast-healing predecessor35330918 was reproduced before compiling aa.cpp. Existing world, rules, Guise item cache4c5a40e5, spell cache5039b3ab and signed client2026112001 remain paired. Zero-player activation, fresh stopped backup, saved-state/market preservation, twelve workers and reopened access verified. Use E:/EQ_Local_Dev/_worktrees/aa-availability/docs/audits/aa-availability-20261120/; never replay terminal activation or restore player snapshots. Player acceptance remains OPEN.\n\n'
new=new.replace('# Source authority, builds and reloads\n\n','# Source authority, builds and reloads\n\n'+entry,1);changes[p]=(old,new)
p=K/'references/wiki.md';old=p.read_text(encoding='utf-8');entry='## AA availability · November20 published\n\nRelease20261120-aa-availability-v1 changes Multiclass, Recent changes and search over exactly reproduced fast-healing-v1. All631public outputs and private denials verified; rollback rehearsed and services/client preserved. The guide explains the six-class Mastery prerequisite correction, retained caster requirement, relog and Recommended filtering. Home/Features/commands and generated catalogs reviewed with no further impact. Historical global source drift stays marked for review. Evidence: E:/EQ_Local_Dev/_worktrees/aa-availability/docs/audits/aa-availability-20261120/.\n\n';new=old.replace('# Official player wiki and Features\n\n','# Official player wiki and Features\n\n'+entry,1);changes[p]=(old,new)
p=K/'references/sources.json';old=p.read_text(encoding='utf-8');m=json.loads(old)
paths=['server-mods/code/common/aa_availability.h','server-mods/code/zone/aa.cpp','tools/tests/test_aa_availability.py','docs/audits/aa-availability-20261120/README.md','docs/audits/aa-availability-20261120/audit.json','docs/audits/aa-availability-20261120/build.json','docs/audits/aa-availability-20261120/production-verified.json','docs/audits/aa-availability-20261120/wiki-public-verification.json']
entries=[dict(root=W.as_posix(),path=n,role='Reviewed AA availability source/test/release; player acceptance OPEN',revision=rev,sha256=hashlib.sha256((W/n).read_bytes()).hexdigest()) for n in paths]
for topic,values in m['topics'].items():
 for e in values:
  if e['path']=='server-mods/code/zone/aa.cpp':e.update(entries[1])
m['topics']['aa-availability']=entries;changes[p]=(old,json.dumps(m,indent=2,ensure_ascii=False)+'\n')
p=K/'SKILL.md';old=p.read_text(encoding='utf-8');new=old.replace('| Quick Buff AA hotkey |','| AA availability, prerequisites and unchanged rank policy | [Multiclass and progression](references/multiclass.md) / `aa-availability` |\n| Quick Buff AA hotkey |',1);changes[p]=(old,new)
patch=''.join(''.join(difflib.unified_diff(o.splitlines(True),n.splitlines(True),fromfile=str(p),tofile=str(p))) for p,(o,n) in changes.items())
(A/'installed-skill.patch').write_text(patch,encoding='utf-8')
for p,(old,new) in changes.items():p.write_text(new,encoding='utf-8',newline='\n')
print('Updated AA availability knowledge and reviewed source fingerprints')
