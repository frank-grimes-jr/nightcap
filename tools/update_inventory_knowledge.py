"""Refresh only this release's installed knowledge after observed publication."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
from inventory_release_support import ROOT,HERE

SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    native=json.loads((HERE/'native-deployment.json').read_text(encoding='utf-8'))
    client=json.loads((HERE/'client-public-verification.json').read_text(encoding='utf-8'))
    wiki=json.loads((HERE/'wiki-public-verification.json').read_text(encoding='utf-8'))
    assert native['gateway_open'] and client['hosted'] and client['release']==2026111202 and wiki['status']=='PASS'
    original={p:(SKILL/p).read_text(encoding='utf-8') for p in ('references/client.md','references/operations.md','references/wiki.md','references/sources.json')}
    updated=dict(original)
    client_note='''## Inventory combat summary and heroics — November12 live testing

Owner authorized main/live publication before acceptance. PR434/ab2e8d87 and
E:/EQ_Local_Dev/_worktrees/heroic-stats-inventory own source and
docs/releases/heroic-stats-inventory-20261112/ owns exact build/rollout/client/
wiki receipts and QA. Heroic mechanics were already enabled (standard1.0,
Nightcap melee/spell scaling true); bucket scaling=false does not disable them.
Never enable the optional direct INT-to-Spell Damage/WIS-to-Heal rules to fix UI.

Main Inventory has AC/MIT/AVD/ATK/DMG/HEAL above XP/attributes. Green current,
white /actual cap and gold signed heroics use server getters; GetMax* includes
heroic allowance, and heroics are already included rather than added again.
+0 and negative heroics retain sign. MIT uses cached GetMitigationAC (not fresh
ACSum); AVD uses GetTotalDefense (not item GetAvoidance), with -1 shown Auto.
Ratings are not percentages; opponent penetration/PvP/sitting/other checks apply.
AC is conventional native display; ATK GetTotalATK; DMG/HEAL capped stat bonuses.

Separate negotiated NCIV1 has26int32fields plus existing identity/sequence;
legacy NCST1/33fields remain unchanged. #nightcapui inventory alone requests
both frames under existing3sec throttle; DLL at most1/sec while rendered,
8sec expiry/identity/replay checks, silent chat and state reset. Missing/stale
values are gray --; current/heroic/cap colors explicit. No Client members/vtable,
rules/schema/ItemData/cache/quest/player or bonus-calculation change.

tools/client_inventory_summary_ui.py owns both normal-generator and scoped
published-byte transform:22new labels,40px wider column/window and56px extra
height with normal font/scroll access. Preserve equipment semantics and other
tabs/single Shield Block total. Tests test_client_character_stats.py,
test_inventory_stats_{capture,protocol}.py and equipped-stats-labels.cpp execute
real collection/format/label/chat/reset paths.16focused/11runtime groups/
120exact guards,18Linux rollout and21Linux publisher faults pass. Independent
review findings resolved; owner declined extra cross-model. Pixels, equip/buff/
shield refresh, large values and zone/relog/skin lifecycle remain owner QA.

Current source was transplanted only onto authenticated retained DoT source;
zone7b61b5ac reproduces before command-unity rebuild to b737e641. World95fc228a,
shared_memoryb60c4dfc and all newer Quick Buff/Imitate Death/DoT/Hate policies
remain. Do not replace shipping Client layout from unrelated newer Git features.
Signed2026111202/proxy0.13.6 publishes DLL/catalog/Inventory XML only;145other
descriptors/URLs, Quick Buff strings, config/history/tombstones stay exact.
All148canonical HTTPS assets/signature/pair verify. Exit EQ/use launcher Play.
Pair native zone and signed client; rule/quest reload is insufficient. Native
rollout uses supported whole-runtime shutdown, zero players, admission drain,
fresh stopped backup, saved-state/market/preservation/failure-hold gates. Never
kill one OVH zone, replay a terminal action or restore old player snapshots.
Recovery pairs retained image/current data and higher-counter client assets.
The immutable stage's client_channel_sha256 is the prepublication1201 baseline;
files['client/channel.json'] and paired-deployed.json own the current1202 hash.
Inherited Quick Buff console labels/deployed.json are not this pair's authority.

Wiki publishes only four owning guides/history plus search; all614hashes/headers
and five private denials verify,609outputs retained.43authored guides/Home/
Features/commands/generated catalogs assessed. Unrelated global refresh drift
stays review-required; visible player/combined balance acceptance remains OPEN.

'''
    pattern=r'## (?:Heroic stats — November12 production audit; main Inventory candidate|Inventory combat summary and heroics — November12 live testing)\n.*?(?=\n## |\Z)'
    updated['references/client.md'],count=re.subn(pattern,client_note.rstrip()+'\n',updated['references/client.md'],count=1,flags=re.DOTALL)
    assert count==1
    updated['references/client.md']=updated['references/client.md'].replace(
        'Current source E:/EQ_Local_Dev/_worktrees/character-stats-shield-block;',
        'November6 source E:/EQ_Local_Dev/_worktrees/character-stats-shield-block;\ncurrent Inventory/native pairing is the November12 combat-summary section above;',1)
    operations='''## Current native baseline — November12 Inventory live testing

PR434/ab2e8d87, source5dabfb6d; E:/EQ_Local_Dev/_worktrees/heroic-stats-inventory,
docs/releases/heroic-stats-inventory-20261112/. Zoneb737e641 is deployed above the
reproduced DoT7b61b5ac baseline. World95fc228a/shared_memoryb60c4dfc and current
Client/ItemData/cache layouts remain. Four-source read-only UI delta compiles
the two real retained command unity units; no unrelated title gameplay ships.
Signed2026111202/proxy0.13.6 and614-file wiki are verified for live testing.

rollout.py inherits the reviewed deploy/GM locks, zero-player125second drain,
clean whole-runtime stop, fresh stopped backup, saved-state boot model and one
market rotation. Server/client activate paired behind closed gateway; exact
hosted signature/channel verification gates reopen. Standalone publisher is
disabled.21publisher/18rollout Linux faults pass;12workers/hash/health and
preservation checks pass. No player snapshot restore, gameplay/rule/schema/
cache/quest writes. Never kill one production zone or replay terminal actions.
Exit EQ/use launcher Play. Visible player acceptance remains OPEN. Use actual
current deployment/source manifests; newer Git may contain unshipped features.
The stage's client_channel_sha256 is the prepublication baseline. Use the
paired-deployed receipt/files client pin for current state and future wrappers.

'''
    op=updated['references/operations.md']
    op=re.sub(r'## Current native baseline — November12 Inventory live testing\n.*?(?=\n## |\Z)','',op,count=1,flags=re.DOTALL)
    op=op.replace('## Current native baseline — November 12 DoT live QA','## Retained native predecessor — November 12 DoT live QA',1)
    pos=op.index('\n')+1;updated['references/operations.md']=op[:pos]+'\n'+operations+op[pos:].lstrip('\n')
    wiki_note='''## Inventory combat summary — November12 published for live testing

E:/EQ_Local_Dev/_worktrees/heroic-stats-inventory; docs/releases/heroic-stats-inventory-20261112/.
Wiki20261112-inventory-combat-v1 follows paired zoneb737e641/client2026111202.
The current earned-title-preview614outputs reproduce exactly before only
Equipment, Augment guide, Features, Change Log and search change;609outputs
retain exact bytes. All614canonical HTTPS hashes/headers, five private denials,
pointer rollback, all five native/service identities and channel/config inode
preservation verify. No Nginx reload or source-ledger advance.43authored pages,
Home/commands/acquisition/generated catalogs assessed; no item/zone/balance
changes. Keep title gameplay Not released and other unrelated previews intact.
Instructions distinguish actual cap/heroic component and MIT/AVD ratings; native
visible acceptance stays OPEN. Never publish an older whole mirror.

'''
    text=re.sub(r'## Inventory combat summary — November12 published for live testing\n.*?(?=\n## |\Z)','',updated['references/wiki.md'],count=1,flags=re.DOTALL)
    pos=text.index('\n')+1;updated['references/wiki.md']=text[:pos]+'\n'+wiki_note+text[pos:].lstrip('\n')
    manifest=json.loads(updated['references/sources.json'])
    paths=list(json.loads((HERE/'source-fingerprints.json').read_text(encoding='utf-8')))
    paths += ['docs/releases/heroic-stats-inventory-20261112/'+n for n in ('README.md','SPEC.md','native-build.json',
        'native-deployment.json','client-public-verification.json','wiki-publication.json','wiki-public-verification.json','review.json','rollout.py')]
    entries=[{'root':ROOT.as_posix(),'path':p,'role':'Reviewed published Inventory combat/caps/heroics; native visual acceptance OPEN',
              'revision':'PR434/ab2e8d87 + observed paired publication evidence','sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in paths]
    manifest['topics']['heroic-stats']=entries
    for row in manifest['topics'].get('character-stats-display',[]):
        if row['path'] in paths:row.update(next(e for e in entries if e['path']==row['path']))
    manifest['observed_revisions']['heroic_stats_inventory_20261112']='PR434/ab2e8d87; source5dabfb6d; zoneb737e641/client2026111202/proxy0.13.6/wiki20261112-inventory-combat-v1 published and verified; owner visible acceptance OPEN'
    updated['references/sources.json']=json.dumps(manifest,indent=2,ensure_ascii=False)+'\n'
    patch=''.join(''.join(difflib.unified_diff(original[p].splitlines(True),updated[p].splitlines(True),fromfile='a/'+p,tofile='b/'+p)) for p in original)
    (HERE/'installed-skill.patch').write_text(patch,encoding='utf-8',newline='\n')
    if args.apply:
        for p in updated:
            assert (SKILL/p).read_text(encoding='utf-8')==original[p]
            (SKILL/p).write_text(updated[p],encoding='utf-8',newline='\n')
    print('Installed published-release knowledge updated' if args.apply else 'Exact published-release skill patch saved')


if __name__=='__main__':main()
