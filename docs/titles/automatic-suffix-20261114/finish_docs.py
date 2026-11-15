"""Update current status from real terminal runtime and public HTTPS evidence."""
import json
from pathlib import Path
from control import HERE,ROOT

live=json.loads((HERE/'production-verified.json').read_bytes())
public=json.loads((HERE/'wiki-public-verification.json').read_bytes())
assert live['result']==public['result']=='PASS' and live['gateway_open'] and live['workers']==12
successor=json.loads((HERE/'successor.json').read_bytes()) if live.get('runtime_stage') else None
assert live['binaries']['zone']==(successor['zone'] if successor else json.loads((HERE/'shipping-candidate.json').read_bytes())['zone'])
assert public['release']=='20261114-titles-automatic-suffix-v1' and public['files']==631


def replace(name,old,new):
    path=ROOT/name;body=path.read_text(encoding='utf8');assert body.count(old)==1,(name,old)
    path.write_text(body.replace(old,new),encoding='utf8',newline='\n')


replace('docs/titles/automatic-suffix-20261114/README.md','**Built and tested; live activation pending.**',
    '**Active on production; all twelve open workers verified.**\n[Runtime verification](production-verified.json) · [Preservation proof](activation-summary.json) ·\n[Public wiki checks](wiki-public-verification.json). Native player UI acceptance remains OPEN.')
if successor:
    replace('docs/titles/automatic-suffix-20261114/README.md','## Exact native player QA — OPEN',
        '''## Current compatible successor

The title release deployed and reopened successfully. The separately authorized
Classic augment release then reproduced its exact04cd4b50 baseline and changed
only augment socket/swap handling. Current zone289df4f2 retains automatic titles,
the current rest world/rules, client and caches. `verify_successor.py` authenticates
the exact successor manifest/operator/binaries and both stopped backups, checks
all12open workers and reruns title schema, content, quest and rule preservation.
`successor.json` records the reviewed scope. The original `control.py verify`
expects the title image and must not be used against a later release. No operator
was replayed. Use the current compatible verification and preserve later work.

## Exact native player QA — OPEN''')
replace('docs/titles/automatic-suffix-20261114/README.md',
    'Publication\nwaits for actual live activation; the global historical review ledger is not\nadvanced.',
    'Publication and all631public HTTPS hashes/headers verify after live activation.\nThe global historical review ledger is not advanced.')
replace('docs/README.md',
    '- [Earned titles: live activation, published guide, incident resolution and open player QA](titles/deployment-20261114/README.md)',
    '- [Earned titles: automatic unlocks, matching suffixes, verified runtime/wiki and open native player QA](titles/automatic-suffix-20261114/README.md)')
replace('CHANGES.md','Built/tested; live activation and native player acceptance are separate.',
    'Active on all twelve production workers with the current rest world/rules and client preserved. Public wiki publication is verified; native player UI acceptance remains open.')
replace('docs/status.md','Built and tested automatic milestone/login awards, native title notifications, and equivalent suffix choices. The package rebases over the newer rest world/zone pair and awaits live activation.',
    'Automatic milestone/login awards, native title alerts plus chat, and equivalent suffix choices are active on all twelve open production workers, main PR486/33a7f38a. The current rest world/rules, caches, client and stable awards are preserved. The public Titles guide is published and verified; native player UI acceptance remains open.')
replace('docs/status.md','Palwar’s logged Nagafen victory received named-only credit; opening Titles/#titles reconciles Flamebreaker.',
    'Palwar’s logged Nagafen victory received named-only credit. The later automatic follow-up above checks this credit on login without #titles.')
replace('docs/titles/SPEC.md','prefix/suffix placement and can be changed or cleared. Awarding does not equip.',
    'prefix/suffix placement and can be changed or cleared. Each of the76 catalog\nprefixes also unlocks its matching “the …” suffix through the same permanent\naward and ID. The existing “the Last Lantern” suffix remains. Awarding does not equip.')
replace('docs/titles/SPEC.md','A failed/uncertain cosmetic write is logged and never replayed; it\ncannot cancel an already committed death or alter loot/XP/respawn state.',
    'Failed/uncertain kill-counter writes are logged and never replayed. Durable\nsnapshot checks and idempotent award insertion retry after storage recovers. No\ncosmetic failure cancels an already committed death or alters loot/XP/respawn state.')
old='''Kills and successfully saved skill updates reconcile immediately. Opening the
native Titles list or `#titles [page]` reconciles other/current/historical goals
and displays six progress entries per page. Reconciliation is idempotent through
the `(character_id,title_id)` primary key. Counters use one atomic multi-row
upsert per participant. No destructive player/schema migration is included.'''
new='''Kills and successfully saved skill updates reconcile immediately. Login/zoning,
level saves, committed personal Keeper/High Keep completion and successful final
task9515 persistence schedule automatic checks at the next valid client frame.
Persisted and loaded level must both qualify; skills also use persisted/loaded
raw values. Enclosing transactions defer awards until they end. Transient check
failures retry after30seconds, without replaying kill counters or querying SQL on
idle frames. Unique new awards send the native new-title alert plus chat; an
uncertain committed INSERT acknowledgment may miss its notice. `#titles [page]`
is optional and displays six progress entries. One award/ID unlocks both matching
placements. Counter writes batch the whole credited party in one atomic upsert;
the ordinary kill path remains four SQL statements. No schema migration is needed.
Current source, native build and live proof: automatic-suffix-20261114/README.md.'''
replace('docs/titles/SPEC.md',old,new)
replace('docs/titles/QA.md','[verified November14 release](deployment-20261114/README.md).',
    '[verified automatic-title release](automatic-suffix-20261114/README.md).\nBefore opening Titles or running any command, verify the automatic login, level,\ncompletion and native notification cases in that release’s exact QA checklist.')
path=ROOT/'docs/titles/README.md'
path.write_text('''# Earned titles

All77 achievements unlock automatically, with the native new-title alert and a
chat message. Login/zoning checks recorded goals. Level, persisted skill, qualifying
kill, committed personal dungeon clear and final campaign milestones trigger
checks without opening a window or running a command. `#titles` is an optional
progress browser.

The76 prefixes also unlock matching “the …” suffixes through the same stable
award. For example, Flamebreaker and the Flamebreaker share one achievement.
Existing owners gain the suffix without another grind; the Last Lantern keeps
its existing suffix. Choose a prefix or suffix in Titles when desired. Earning
never changes a worn title or grants stats, XP, items or other power.

Main PR486/33a7f38a and all twelve production workers are verified with matching
rest world, unchanged caches and signed client2026111301. The public
[Titles guide](https://wiki.nightcapgame.org/titles.html) is verified across all
631HTTPS files. Native picker/nameplate/notification acceptance remains OPEN.

[Current release, source and player QA](automatic-suffix-20261114/README.md) ·
[Contract](SPEC.md) · [Full QA matrix](QA.md). The original activation and scoped
Palwar Nagafen-credit repair remain dated evidence in deployment-20261114/.
That recorded Nagafen goal is now checked automatically on login; no #titles
claim is needed. General totals still begin at activation and are never invented.

Use the reproduced current shipping inputs and the current release's exact
title-only delta. Never deploy an older whole main mirror, replay terminal
operators, kill one production worker or restore a player snapshot. Preserve
all permanent awards/counters and stable IDs during forward recovery.
''',encoding='utf8',newline='\n')
path=ROOT/'docs/ops/nightcap-wiki.md';body=path.read_text(encoding='utf8')
start=body.index('The official wiki serves');end=body.index('\n## Retained hosting snapshots',start)
body=body[:start]+'''The official wiki serves `20261114-titles-automatic-suffix-v1` over
`20261114-titles-active-v1`. Ten title/owning-guide outputs change and621 retain
exact bytes after source reproduction. All631public HTTPS hashes/headers and five
private denials verify. The guide describes automatic awards, native notifications
and equivalent suffixes; #titles is optional. The content-only publisher checks
the active title catalog under the deployment lock and preserves services,
config and client. Native player UI acceptance stays open.
[Source and recovery](../titles/automatic-suffix-20261114/README.md) ·
[Public verification](../titles/automatic-suffix-20261114/wiki-public-verification.json).
'''+body[end:]
path.write_text(body,encoding='utf8',newline='\n')
path=ROOT/'docs/titles/wiki-impact.md';body=path.read_text(encoding='utf8')
end=body.index('## Historical November12 source/publication review')
body='''# Current title wiki impact · November14

The631-file public titles-active-v1 source reproduced exactly. Ten outputs now
describe automatic login/milestone awards, native alerts plus chat, and equivalent
suffixes: Titles, Commands, Features, Combat, Dungeon Modes, Multiclass,
Tradeskills, Adventure Journal, Change Log and search. The other621files retain
exact bytes. All631HTTPS hashes/headers and five private denials verify.
[Current release and publication evidence](automatic-suffix-20261114/README.md).

Whole-wiki review: all77exact requirements and76prefix/77suffix choices agree.
Home's existing goal paths need no release announcement. No generated item/zone,
catalog/acquisition/reward value, Build Lab or Loot Finder behavior changes.
Current-main authored guides are aligned without republishing that older mirror.
The rest guide's separate pending publication is not bundled into this title
release. Historical source drift remains REVIEW REQUIRED; no global ledger
advance. Native picker/nameplate/notification acceptance stays OPEN.

'''+body[end:]
path.write_text(body,encoding='utf8',newline='\n')
print('Current title, status, contract, QA and wiki runbook updated from terminal proof')
