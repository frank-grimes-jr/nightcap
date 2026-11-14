"""Preimage-checked installed knowledge refresh after real runtime/wiki proof."""
import difflib
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
sha=lambda b:hashlib.sha256(b).hexdigest()


def main(apply):
    live=json.loads((HERE/'production-verified.json').read_bytes())
    public=json.loads((HERE/'wiki-public-verification.json').read_bytes())
    repair=json.loads((HERE/'palwar-correction.json').read_bytes())
    assert live['result']=='PASS' and live['workers']==12 and live['gateway_open'] and live['title_catalog_enabled']
    assert public['result']=='PASS' and public['release']=='20261114-titles-active-v1' and public['files']==631
    assert repair['result']=='PASS' and not repair['generic_counters_written']
    names=['references/titles.md','references/operations.md','references/wiki.md','references/sources.json']
    old={name:(SKILL/name).read_bytes() for name in names}
    titles='''# Earned titles — active on production November 14, 2026

Main PR475/b824e0d2 activates77 permanent cosmetic titles. The shipping zone is
f35b4e3db6dd87f2eb5e62a916543508988df87c53ae9355ee2f4fae53fe2602 over
the exactly reproduced fixed-AA82d5e2d2 binary, preserving completed prismatic
content, all144 link inputs and eleven unchanged command archive members.
All12 workers, enabled catalog1, public #titles access0, clean logs, stopped
backup and native saved-state/market preservation passed with open admissions.
Signed client2026111301, world/shared_memory and current caches stay paired;
no client, quest or rule update. Native rendered/player acceptance remains OPEN.

Current source/evidence: E:/EQ_Local_Dev/_worktrees/earned-titles,
docs/titles/deployment-20261114/. The title-only shipping feature.patch and
shipping-candidate.json are authoritative; newest main's whole native files can
include unrelated unshipped work. Four compiled policy/actual adapter groups,
real MariaDB migration and1/6/72-member bursts, twelve release fault controls,
seven bounded-continuation cases and publisher control regression pass.

The first attempt held PRE-SQL after its stopped backup because a newly added
hook called world player-count RPC while the game was stopped. resume.py is a
one-shot exact-hold continuation with a second fresh backup and every original
boot/preservation gate. Original operator, first backup and resolved hold remain
retained. Never replay deploy/resume or use the original recovery CLI after
opening. Corrected recovery uses real RPC while running and verifies clean
stopped state otherwise. Forward repair after activity preserves all awards and
counters; no old player snapshot restore and no individual zone-worker kills.

Native selection/HasTitle authorizes per-character awards at stable IDs
1900000000–1900000999. Existing native IDs in that range suspend the system.
Three InnoDB tables own settings, counters and awards; catalog_version1/enabled1
fence counting/grants. No stats, items, currency, XP or automatic worn-title
replacement. Disabling retains awards/counters/profile titles; never reuse IDs.

Slayer totals100/1000/10000; undead100/1000/5000; giants100/1000;
dragons1/10/100. Finalized natural, unowned non-gray deaths credit ordinary
status0/GMoff loaded, connected, alive party/raid members within200units.
Counters start at activation, saturate10000 and use four ordinary SQL statements
regardless of party size. Unique first-award inserts add statements and notify
once; failed/uncertain writes log without replay or combat veto. Body types own
families. Home-zone Nagafen earns Flamebreaker, Vox Frostbreaker; both earn
Dragonslayer. Personal Keeper boss history can recover named goals, never totals.

Palwar's public Nagafen kill is independently logged as event20094/character29,
NPC32040/zone32 at2026-11-14 19:40:51UTC, before activation. The guarded repair
restores only named counter100; no general/dragon totals, direct award or worn
title write. Open Titles/#titles lets native reconciliation award Flamebreaker
and send the first-award notification. Actual receipt: palwar-correction.json;
do not claim its visible notification was observed.

Personal completed_at>0 Keeper ledgers own full clears. Raid mode1 across all21
Classic dungeons earns Conqueror of Classic; normalize historical Hate76 to186.
Chapterhouse760/Kael113 and partial/global/other-member credit do not substitute.
34skill titles require level50+ and persisted/loaded raw skill at highest held-
class native level50 cap; zero caps/skill bonuses do not qualify. Existing
race/class/crafting/New Tanaan rules remain. Seven crafts earn Master Artisan;
completed_tasks9515/activity-1 earns the Last Lantern. Awards survive class
release. Titles window/#titles recovers existing goals; qualifying kills and
successfully saved skill updates reconcile immediately.

Wiki20261114-titles-active-v1 is published at
https://wiki.nightcapgame.org/titles.html after exact631-file public-source
reproduction. Six changed outputs retain625 exact files. All631 HTTPS hashes/
headers and five private denials pass; publisher rollback/service/config/channel
guards pass. Public prose says available; internal status is Live testing.
Use retained artifacts/titles-live-20261114/wiki/wiki-source for the next release,
not the stale main mirror. Whole-wiki historical drift stays REVIEW REQUIRED;
no global ledger advance. Native picker/nameplate/notification QA remains OPEN.
'''
    result={'references/titles.md':titles.encode()}
    operations=old['references/operations.md'].decode()
    start=operations.index('## Current native production baseline')
    end=operations.index('## Previous native production baseline',start)
    assert 'fixed AA duration' in operations[start:operations.find('\n',start)],'Current native authority changed: review before replacing it'
    operations=operations[:start]+'''## Current native production baseline · earned titles

Main PR475/b824e0d2, zone f35b4e3db6dd87f2eb5e62a916543508988df87c53ae9355ee2f4fae53fe2602 over reproduced fixed-AA82d5e2d2. Twelve open workers and enabled catalog1/#titles access0 verify. Completed prismatic data, signed client2026111301, native pair and caches are preserved. Current authority: E:/EQ_Local_Dev/_worktrees/earned-titles/docs/titles/deployment-20261114/. Original pre-SQL stopped-world RPC hold was resolved by the exact one-shot resume with a second fresh stopped backup; never replay terminal operators or restore player snapshots. Corrected recovery uses RPC only with a running world. See titles.md for named-counter correction and native player QA boundary.

'''+operations[end:]
    result['references/operations.md']=operations.encode()
    wiki=old['references/wiki.md'].decode()
    start=wiki.index('## Earned titles — November12 wiki preview published')
    end=wiki.find('\n## ',start+1)
    if end<0:end=len(wiki)
    wiki=wiki[:start]+'''## Earned titles · November 14 published and active

Wiki20261114-titles-active-v1 reproduces all631 published archery/Backstab files, changes only Titles, commands, Combat, Adventure Journal, Change Log and search, and retains625 exact files. All631 public HTTPS hashes/headers and five private denials verify. Runtime f35b4e3d/catalog1 is enabled with12open workers; native player acceptance remains OPEN. Public prose says available, while internal status remains Live testing. The publisher rechecks current enablement/schema/command under the shared deployment lock, rehearses pointer rollback and preserves services/config/client. Current source: E:/EQ_Local_Dev/_worktrees/earned-titles/artifacts/titles-live-20261114/wiki/wiki-source; evidence and one-shot operators in docs/titles/deployment-20261114/. Never replay the terminal publisher or publish an older main mirror. No generated item/zone/acquisition values changed and no global ledger advance.

'''+wiki[end:]
    result['references/wiki.md']=wiki.encode()
    sources=json.loads(old['references/sources.json'])
    sources['observed_revisions']['titles_active_20261114']='main PR475/b824e0d229c56737753321bcded38879bbf41102; native f35b4e3d; 12 open workers; named-only Palwar repair; native player QA OPEN'
    sources['observed_revisions']['titles_wiki_active_20261114']='20261114-titles-active-v1; 631 HTTPS hashes/headers and 625 retained files; no global ledger advance'
    paths=['tools/earned_titles.py','server-mods/code/common/earned_title_policy.h','server-mods/code/common/earned_title_catalog.h',
        'server-mods/code/zone/earned_titles.h','server-mods/code/zone/earned_titles.inc','server-mods/code/zone/titles.cpp',
        'server-mods/code/zone/attack.cpp','server-mods/code/zone/client.cpp','server-mods/code/zone/command.cpp','server-mods/code/zone/command.h',
        'tools/tests/test_earned_titles.py','tools/tests/earned_titles_service_fixture.cpp','docs/titles/setup.sql','docs/titles/SPEC.md','docs/titles/QA.md','docs/titles/README.md','wiki/articles/titles.json']
    release_paths=['README.md','INCIDENT.md','feature.patch','shipping-candidate.json','source-delta.json','schema.py','release.py','release-original.py','staged.json','test_release.py',
        'resume.py','test_resume.py','resume-staged.json','activation-summary.json','production-verified.json','verify_live.py','palwar.py','palwar-correction.json',
        'wiki.py','wiki_publish.py','test_wiki_publication.py','wiki-content-checks.json','wiki-publication.json','wiki-public-verification.json']
    paths+=['docs/titles/deployment-20261114/'+p for p in release_paths]
    sources['topics']['titles']=[dict(root=str(ROOT).replace('\\','/'),path=p,
        role='Reviewed title implementation, active release evidence or explicit player QA boundary',sha256=sha((ROOT/p).read_bytes())) for p in paths]
    result['references/sources.json']=(json.dumps(sources,ensure_ascii=False,indent=2)+'\n').encode()
    patch=''.join(''.join(difflib.unified_diff(old[n].decode().splitlines(True),result[n].decode().splitlines(True),fromfile=n,tofile=n)) for n in names)
    (ROOT/'artifacts/titles-live-20261114/installed-knowledge.patch').write_text(patch,encoding='utf8',newline='\n')
    if apply:
        assert all((SKILL/n).read_bytes()==old[n] for n in names),'Concurrent skill update: recapture and merge'
        for name,data in result.items():(SKILL/name).write_bytes(data)
    print('Installed knowledge updated' if apply else 'Exact installed knowledge patch prepared')


if __name__=='__main__':
    assert sys.argv[1:] in [[],['--apply']]
    main(bool(sys.argv[1:]))
