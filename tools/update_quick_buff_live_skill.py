"""Update only reviewed Quick Buff knowledge after verified live publication."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/releases/quick-buff-20261112'

def section(text,heading,replacement):
    start=text.index('## '+heading);end=text.find('\n## ',start+3)
    return text[:start]+replacement.rstrip()+'\n\n'+(text[end+1:] if end>=0 else '')

def main():
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args()
    skill=Path('C:/Users/verre/.codex/skills/nightcap-development')
    production=json.loads((OUT/'production-verification.json').read_text(encoding='utf-8'))
    client=json.loads((OUT/'client-public-verification.json').read_text(encoding='utf-8'))
    wiki=json.loads((OUT/'wiki-public-verification.json').read_text(encoding='utf-8'))
    assert production['status']=='PASS' and production['gateway_open']
    assert client['hosted'] and client['release']==2026111201 and wiki['status']=='PASS' and wiki['files']==613
    names=['SKILL.md']+['references/'+n for n in ('multiclass.md','operations.md','client.md','wiki.md','sources.json')]
    before={n:(skill/n).read_text(encoding='utf-8') for n in names};after=dict(before)
    after['SKILL.md']=before['SKILL.md'].replace('Quick Buff AA hotkey candidate','Quick Buff AA hotkey')
    quick='''## Quick Buff — November12 deployed for live QA

Owner authorized main/live testing; PR422/a2ae50f0 contains the reviewed release.
Family48/ranks147–149 are an earned activated hotkey: immediately attempt eligible
memorized duration buffs on self, normal group/pet delivery, one floor(maxmana/2)
cost (minimum1for positive pool), full cost required, zero reuse. All existing
rank ownership/costs/class masks stay; passive buff haste is replaced. Native
canonical held-class/current-level/scribed eligibility, caster/zone/target checks,
reagents, stacking and events remain. Completion failure does not refund the
activation. Empty/ineligible bar costs nothing. Snapshot/dedup the bar; reject
death/unconsciousness, existing casting/recovery and reentry. No new AA grants.

common/quick_buff.h projects active metadata on AA load; spell8 is presentation
only and never cast. zone/aa.cpp authorizes before CastQuickBuff; aa_quick_buff.inc
debits once before synchronous native zero-time/zero-individual-mana casts.
spells.cpp limits reuse/recovery bypass to active Quick Buff. bard_component_mode
retains instrument-type validation for primary/secondary Bard without component
consumption or a new song pulse/melody. Other spell/item/discipline/AA clocks stay.
Client gained a member: full zone/common/GM/Lua/Perl rebuild is mandatory.

Shipping zone1fe268a18c45190f43ea25290c95ad852561029da5cacb024d7c99a91d40abd4
preserves Augment icon world95fc228a/shared_memoryb60c4dfc, metadata-aware systems,
newer retained Hate catalog mapping/count223 and all quests/rules/cache/content.
Git's older176header must not replace that native dependency. Reproduction patch:
docs/releases/quick-buff-20261112/retained-native-overlay.patch. The isolated
command_augstats declaration only repairs the source snapshot; no body/layout
change. Shipping predecessor reproduced; full-build.json pins2856source files,
full target and stripped ELF identity. Native method/AA packet/reagent tests and
28Linux publisher/operator fault checks pass; fresh-context findings resolved.

Supported whole-runtime deployment uses deploy/GM locks, zero clients,125second
auth drain, clean stop, fresh stopped full backup, exact normal saved-state boot
and one-market-rotation checks. Signed text publishes while admissions remain
closed; exact channel hash gates reopening. No player snapshot/data restoration.
After any public counter, recover client text at a higher counter with current
unrelated assets; never replay terminal actions. AA reload alone cannot install C++.

Signed2026111201 changes dbstr147types2/3/4 only;147other descriptors/URLs and the
proxy/catalog/config pair remain. Exit EQ/launcher Play, then AA window → Quick
Buff → Make Hotkey. No SQL/schema/rule/cache/quest/DLL/new spell-asset delta.
Source E:/EQ_Local_Dev/_worktrees/quick-buff-hotkey; source/tests include
tools/{quick_buff_client.py,tests/test_quick_buff.py,tests/test_quick_buff_reagents.py,
tests/test_aa_cooldown_identity.py,tests/test_quick_buff_rollout.py}.
Exact source/proof/rollout/recovery/player steps: docs/releases/quick-buff-20261112/.
Server/client/wiki verification is complete; native hotkey/delivery, ordinary
player and combined-build balance acceptance remain OPEN. No automatic acceptance.
'''
    after['references/multiclass.md']=section(before['references/multiclass.md'],'Quick Buff — November 12 source candidate, not deployed',quick)
    op='''## Current native baseline — November12 Quick Buff live QA

PR422/a2ae50f0; E:/EQ_Local_Dev/_worktrees/quick-buff-hotkey,
docs/releases/quick-buff-20261112/. Full zone1fe268a1 preserves current
world95fc228a/shared_memoryb60c4dfc and Augment icon repair; all12workers and
native/service identities verify. No content/rule/schema/cache/quest/player-data
rewrite. Authenticated full source retains newer Hate mapping/count223 despite
older Git176header; exact reproduction overlay and2856source pins are retained.
Full zone/common/GM/Lua/Perl build and stripped ELF identity pass. Client layout
changed: do not replace this full build with a two-TU retained-object relink.

Use this release's one-shot rollout.py and immutable stage receipts, never old
terminal operators. Deployment/GM locks, zero-player125second admission drain,
clean whole-runtime stop, fresh stopped full backup, normal saved boot/one market
rotation and exact preservation checks precede publication/reopening. Signed
client2026111201 is checked while admissions stay closed. Failure holds access;
no player snapshot restore. Client recovery requires higher signed counter and
current unrelated assets. Never kill one production zone. Gameplay/balance and
visible native hotkey acceptance remain open; publication is not acceptance.

'''
    original=before['references/operations.md'].replace('## Current native baseline — November 12 augment icons','## Augment icon repair — November12 deployed')
    first,rest=original.split('\n',1);after['references/operations.md']=first+'\n\n'+op+rest.lstrip('\n')
    client_note='''## Quick Buff — November12 signed text published

Signed2026111201 replaces2026110701; only dbstr_us.txt changes. Types147/2and3
add Quick Buff labels;147/4explains instant memorized buffs,50%maximum mana and
zero reuse. All other strings,147asset descriptors/URLs, proxy0.13.5/catalog/
config, previous notes and tombstones remain. Local signing seed never uploaded.
Shipped-key signature, actual executable/proxy/catalog pair and all148canonical
HTTPS sizes/hashes verify. Fully exit EQ/use launcher Play, then Make Hotkey in
the AA window. Paired zone1fe268a1 is deployed; actual native appearance/delivery
and owner gameplay/balance acceptance remain OPEN. No protected client write.
Proof/source: quick-buff-hotkey worktree, docs/releases/quick-buff-20261112/;
tools/quick_buff_client.py + prepare_client.go/verify_client.go. Publisher guards
all retained bytes and changes channel last while gateway is closed under the
native release lock; verified channel gates opening. Newer public counters require
forward repair, retaining all current unrelated assets and player activity.

'''
    first,rest=before['references/client.md'].split('\n',1);after['references/client.md']=first+'\n\n'+client_note+rest.lstrip('\n')
    wiki_note='''## Quick Buff — November12 published for live testing

Wiki20261112-quick-buff-v1 replaces20261112-augment-icons-v1. Exact613previous
public outputs reproduced before Combat, Multiclass, Features, In development,
Change Log and search change;607files retained. All42authored article/Home/
command/catalog/generated-page impacts reviewed; no item/zone/acquisition values
change. Features keeps the character-systems grouping. Instructions name native
Make Hotkey, immediate memorized buffs,50%maximum mana, zero reuse, normal group/
pet delivery and spell restrictions. All613HTTPS hashes/security headers and
five private/source denials pass. Pointer rollback rehearsed; private downloads,
config and all five service identities retained. No Nginx reload. Global unrelated
source drift remains REVIEW REQUIRED; no blanket ledger advance. Exact public
source is the authenticated artifact tree, not an older full Git mirror. Evidence
and preparation/publishing tools: quick-buff-hotkey/docs/releases/quick-buff-20261112/.
Native hotkey/delivery and balance acceptance remain OPEN.
'''
    after['references/wiki.md']=section(before['references/wiki.md'],'Quick Buff — November 12 unpublished candidate',wiki_note)
    manifest=json.loads(before['references/sources.json'])
    manifest['observed_revisions'].pop('quick_buff_candidate_20261112',None)
    revision='maina2ae50f0/PR422 + verified November12 release receipts; native sourcea78fa630 plus retained-native-overlay.patch'
    manifest['observed_revisions']['quick_buff_deployed_20261112']=revision
    paths=['server-mods/code/'+n for n in ('common/quick_buff.h','zone/aa.cpp','zone/aa_quick_buff.inc','zone/client.h','zone/spells.cpp')]
    paths+=['tools/'+n for n in ('quick_buff_client.py','tests/test_quick_buff.py','tests/test_quick_buff_reagents.py','tests/test_aa_cooldown_identity.py','tests/test_quick_buff_rollout.py')]
    paths+=['docs/releases/quick-buff-20261112/'+n for n in ('README.md','rollout.py','full-build.json','production-verification.json','client-public-verification.json','wiki-public-verification.json','retained-native-overlay.patch')]
    entries=[dict(root=ROOT.as_posix(),path=n,role='Reviewed deployed Quick Buff implementation/test/pairing evidence; owner acceptance OPEN',revision=revision,sha256=hashlib.sha256((ROOT/n).read_bytes()).hexdigest()) for n in paths]
    manifest['topics']['quick-buff']=entries
    for topic,topic_files in {'operations':['production-verification.json','full-build.json','rollout.py'], 'client':['client-public-verification.json'], 'wiki':['wiki-public-verification.json']}.items():
        selected=[e for e in entries if any(e['path'].endswith('/'+n) for n in topic_files)]
        manifest['topics'][topic]=selected+[e for e in manifest['topics'][topic] if e['path'] not in {v['path'] for v in selected}]
    after['references/sources.json']=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
    patch=''.join(''.join(difflib.unified_diff(before[n].splitlines(True),after[n].splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in names)
    (OUT/'installed-live-skill.patch').write_text(patch,encoding='utf-8',newline='\n')
    if a.write:
        for n,value in after.items():(skill/n).write_text(value,encoding='utf-8',newline='\n')
    print(json.dumps(dict(status='installed' if a.write else 'prepared',files=len(after),patch_bytes=len(patch.encode()))))
if __name__=='__main__':main()
