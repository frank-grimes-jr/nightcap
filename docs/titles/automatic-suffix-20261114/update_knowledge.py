"""Merge current installed knowledge, guarded by terminal runtime/wiki evidence."""
import difflib
import hashlib
import json
from pathlib import Path
import sys
from control import HERE,ROOT,ART

SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
sha=lambda b:hashlib.sha256(b).hexdigest()


def section(body,heading,text):
    start=body.index(heading);end=body.find('\n## ',start+1)
    if end<0:end=len(body)
    return body[:start]+text.rstrip()+'\n\n'+body[end:].lstrip('\n')


def main(apply):
    live=json.loads((HERE/'production-verified.json').read_bytes())
    public=json.loads((HERE/'wiki-public-verification.json').read_bytes())
    assert live['result']==public['result']=='PASS' and live['gateway_open'] and live['workers']==12
    successor=json.loads((HERE/'successor.json').read_bytes()) if live.get('runtime_stage') else None
    assert live['binaries']['zone']==(successor['zone'] if successor else json.loads((HERE/'shipping-candidate.json').read_bytes())['zone'])
    assert public['release']=='20261114-titles-automatic-suffix-v1' and public['files']==631
    names=['references/titles.md','references/operations.md','references/wiki.md','references/sources.json']
    old={n:(SKILL/n).read_bytes() for n in names}
    titles='''# Earned titles — automatic awards and suffixes active November 14, 2026

Main PR486/33a7f38a activates automatic checks and matching suffixes for all77
achievements. Zone04cd4b50d891d72f71eda40a45c76160fb3e21608bebe89cb687e318f2d7797e
preserves the exactly reproduced rest d9ab889a baseline, world eafe4507, zero-delay
rest rules, current caches and signed client2026111301. Twelve open workers,
clean logs, fresh stopped backup, native saved-state/market preservation and
closed award/counter digests verify. Native rendered/player acceptance is OPEN.

The separately authorized Classic augment release PR489/acb232e1 then reproduced
04cd4b50 exactly and changed only augment socket/swap handling. Current zone
289df4f2037bf4e7348278442ce43db0bba498a35680adc6d1fbe06e5b0869b8 retains
automatic titles. successor.json/verify_successor.py bind its archive manifest,
operator, build, reviewed patch and title parent, then check current12workers,
both stopped backups and title/content/rule preservation. Do not run the original
title-image verifier against a successor. The initial busy-lock check safely
declined before doing any verification or mutation.

Current source/evidence: E:/EQ_Local_Dev/_worktrees/earned-titles,
docs/titles/automatic-suffix-20261114/. feature.patch, source-delta.json and
shipping-candidate.json describe nine effective source files/seven units over
the current rest PCH/VFS/common library. All144 link inputs/current command
archive are retained. The earlier f35b4e3d-based candidate was never staged.
predecessor-recompile.json reuses exact original recompilations only after
checking all seven incumbent objects and nine source hashes are identical.
Five focused compiled adapter/policy groups, four actual isolated MariaDB checks,
ten rollout fault controls and fresh independent source review pass.

Native selection/HasTitle authorizes permanent per-character awards at stable
IDs1900000000–1900000999; native ID collisions suspend the system. Three InnoDB
tables own settings/counters/awards; catalog_version1/enabled1 fence writes.
No new ID/schema/client/rule, Client layout change, power or automatic worn-title
replacement. Disabling retains awards/counters/profile titles; never reuse IDs.
The76 prefixes expose their matching “the …” suffix through the same award and
ID; the Last Lantern retains its suffix. Totals:77achievements,76prefix choices,
77suffix choices. Existing owners need no repeat grind. Name/AppendEligible
and native authorization use the same stable ID; all forms fit31bytes.

Qualifying kills and successfully saved skill updates reconcile immediately.
Login/zone completion, level save, committed personal Keeper/High Keep completion
and persisted final task9515 enqueue via RequestCheck. Pulse runs after existing
client validity/disconnect checks; pending monotonic time uses entity variable
nightcap:title-check-at, not a raw pointer map or new Client field. Idle frames
do no SQL. Enabled reads control plus @@in_transaction together; outer
transactions defer checks. Transient check/storage failures retry after30seconds.
Persisted and loaded level must both qualify; raw skills likewise use the lower
saved/loaded value and highest held-class native level50 cap. SetLevel failed
saves cannot award prematurely. Successful primary task9515 persistence queues
before optional cleanup; committed dungeon/rescue credit queues before projection.
Unique award inserts send NotifyNewTitlesAvailable/OP_NewTitlesAvailable plus
yellow chat. Existing awards suppress repeat notices. A committed INSERT with
lost acknowledgment may miss its notice; there is no durable notification outbox.
#titles remains an optional progress browser; it is never needed to earn titles.

Slayer totals100/1000/10000; undead100/1000/5000; giants100/1000;
dragons1/10/100. Finalized natural unowned non-gray deaths credit ordinary
status0/GMoff loaded, connected, alive party/raid members within200units.
Body types own families; counters start at activation and saturate10000.
Ordinary kills stay four SQL statements for any party/raid size. Unique grants
add statements. Counter writes are never replayed after uncertain failures;
outer transaction writes schedule award readback without replaying the counter.
No cosmetic failure cancels a committed death or changes loot/XP/respawn.
Home-zone Nagafen earns Flamebreaker, Vox Frostbreaker, both Dragonslayer.
Personal Keeper boss history can recover named goals, never general totals.

Palwar's preactivation Nagafen kill event20094/character29/NPC32040/zone32 at
2026-11-14 19:40:51UTC is preserved in deployment-20261114/palwar-correction.json.
That guarded repair seeded only named counter100, no direct award/general count
or worn profile. Automatic login now checks that goal; no #titles claim is needed.
No visible Palwar notification has been observed by the release checks.

Personal completed_at>0 Keeper ledgers own clears. All21Classic Raid mode1
dungeons earn Conqueror of Classic; normalize historical Hate76 to186.
Chapterhouse760/Kael113 and partial/global/other-member credit do not substitute.
34skill titles require level50+ and legal persisted/loaded raw caps; zero caps
and bonuses do not qualify. Existing race/class/crafting/New Tanaan rules remain.
Seven crafts earn Master Artisan; completed_tasks9515/activity-1 earns the Last
Lantern. Permanent awards survive class release.

release.py authenticates the prior rest operator/manifest/receipt, unwraps the
old title migration's late-bound content normalizer and restores its original
backup function, retaining independent schema/catalog/access guards. No SQL
migration is replayed. Clean stopped backup proves Running=false/Exit0/notOOM
and closed gateway; never call world RPC while stopped. Recovery uses RPC only
while running. Supported drain/whole-game stop, fresh backup, saved-state expiry
and market rotation gates apply. Never replay terminal operators, kill one zone
worker or restore a player snapshot. After opening preserve awards and repair
forward. Original activation incident/resume remains dated prior evidence only.

Wiki20261114-titles-automatic-suffix-v1 is published at
https://wiki.nightcapgame.org/titles.html after exact631-file reproduction of
titles-active-v1. Ten changed outputs retain621 exact files. All631HTTPS hashes/
headers and five private denials pass, with publisher rollback/service/config/
channel guards. Current retained source is artifacts/titles-live-20261114/
automatic/wiki/wiki-source; never republish the older main mirror. Whole-wiki
historical drift stays REVIEW REQUIRED; no global ledger advance. Native picker,
nameplate and notification acceptance remains OPEN; use the release's exact QA.
'''
    result={'references/titles.md':titles.encode()}
    ops=old['references/operations.md'].decode()
    heading='## Current native production baseline · earned titles'
    assert 'f35b4e3d' in ops[ops.index(heading):ops.index(heading)+500]
    result['references/operations.md']=section(ops,heading,'''## Current native production baseline · automatic titles and suffixes

Main PR486/33a7f38a deployed title-zone04cd4b50 over exactly reproduced rest d9ab889a. Current compatible augment successor PR489/acb232e1 is zone289df4f2037bf4e7348278442ce43db0bba498a35680adc6d1fbe06e5b0869b8; it reproduces04cd4b50 before changing only augment handling. World eafe4507, zero-delay rest rules, current caches and signed client2026111301 remain paired. All12open workers, fresh stopped backups, title-state preservation and saved-state/market checks pass. Automatic login/milestone awards send native alerts plus chat; every prefix shares its award with a matching suffix. Authority: E:/EQ_Local_Dev/_worktrees/earned-titles/docs/titles/automatic-suffix-20261114/, including successor.json/verify_successor.py. No new title SQL schema, rule, client or power. Recovery uses world RPC only while running and never restores player snapshots or replays terminal operators. See titles.md for transaction/retry behavior, Palwar's named-only credit and OPEN native player QA.''').encode()
    wiki=old['references/wiki.md'].decode()
    result['references/wiki.md']=section(wiki,'## Earned titles · November 14 published and active','''## Earned titles · automatic awards and suffixes published November 14

Wiki20261114-titles-automatic-suffix-v1 reproduces the631-file titles-active-v1 source, changes ten title/owning-guide outputs and retains621 exact files. All631public HTTPS hashes/headers and five private denials verify. Title-zone04cd4b50 is retained in compatible augment successor289df4f2 with catalog1 active on12open workers; native UI acceptance stays OPEN. Public prose describes automatic awards, native alerts/chat and equivalent suffix choices, with #titles optional. The content-only publisher rechecks active titles and the exact runtime generation/12workers under the deployment lock, rehearses pointer rollback and preserves services/config/client. Current source: E:/EQ_Local_Dev/_worktrees/earned-titles/artifacts/titles-live-20261114/automatic/wiki/wiki-source; evidence/operators in docs/titles/automatic-suffix-20261114/. Never replay the terminal publisher or use an older main mirror. No generated item/zone/acquisition value changes and no global ledger advance.''').encode()
    sources=json.loads(old['references/sources.json'])
    sources['observed_revisions']['titles_automatic_suffix_20261114']='main PR486/33a7f38a6ee8adacd283f1a30838040ec78eba6d; title-zone04cd4b50 retained in augment successor PR489/acb232e1 zone289df4f2/rest worldeafe4507;12open workers; native player QA OPEN'
    sources['observed_revisions']['titles_wiki_automatic_suffix_20261114']='20261114-titles-automatic-suffix-v1;631HTTPS hashes/headers,621retained files; no global ledger advance'
    paths=['tools/earned_titles.py','server-mods/code/common/earned_title_policy.h','server-mods/code/common/earned_title_catalog.h',
        'server-mods/code/zone/earned_titles.h','server-mods/code/zone/earned_titles.inc','server-mods/code/zone/titles.cpp',
        'server-mods/code/zone/attack.cpp','server-mods/code/zone/client.cpp','server-mods/code/zone/command.cpp','server-mods/code/zone/command.h',
        'tools/tests/test_earned_titles.py','tools/tests/earned_titles_service_fixture.cpp','docs/titles/setup.sql','docs/titles/SPEC.md',
        'docs/titles/QA.md','docs/titles/README.md','wiki/articles/titles.json']
    paths+=['server-mods/code/zone/'+p for p in ['client_packet.cpp','client_process.cpp','exp.cpp','dungeon_service.cpp','highkeep_rescue.inc','task_manager.cpp','task_client_state.cpp']]
    paths+=['docs/titles/automatic-suffix-20261114/'+p for p in ['README.md','native.py','prepare.py','feature.patch','shipping-baseline.json',
        'shipping-candidate.json','source-delta.json','predecessor-recompile.json','release.py','test_release.py','staged.json','review.json',
        'storage.py','storage-tests.json','production-verified.json','activation-summary.json','wiki.py','wiki_publish.py','wiki-candidate.json',
        'wiki-publication.json','wiki-public-verification.json','verify_successor.py','successor.json','test_wiki_publication.py']]
    paths+=['docs/titles/deployment-20261114/'+p for p in ['README.md','INCIDENT.md','palwar-correction.json']]
    sources['topics']['titles']=[dict(root=str(ROOT).replace('\\','/'),path=p,role='Reviewed automatic title/suffix implementation, live evidence or explicit player QA boundary',sha256=sha((ROOT/p).read_bytes())) for p in paths]
    result['references/sources.json']=(json.dumps(sources,ensure_ascii=False,indent=2)+'\n').encode()
    patch=''.join(''.join(difflib.unified_diff(old[n].decode().splitlines(True),result[n].decode().splitlines(True),fromfile=n,tofile=n)) for n in names)
    (ART/'installed-knowledge.patch').write_text(patch,encoding='utf8',newline='\n')
    if apply:
        assert all((SKILL/n).read_bytes()==old[n] for n in names),'Concurrent installed skill update: recapture and merge'
        for n,data in result.items():(SKILL/n).write_bytes(data)
    print('Installed knowledge updated' if apply else 'Exact knowledge patch prepared')


if __name__=='__main__':
    assert sys.argv[1:] in [[],['--apply']]
    main(bool(sys.argv[1:]))
