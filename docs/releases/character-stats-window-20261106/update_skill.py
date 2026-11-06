"""Update reviewed Nightcap knowledge only after verified native/client/wiki release."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SKILL = Path('C:/Users/verre/.codex/skills/nightcap-development/references')


def section(text, heading, replacement):
    start = text.index(heading)
    end = text.find('\n## ', start + len(heading))
    return text[:start] + replacement.rstrip() + '\n' + (text[end:] if end >= 0 else '')


def main(apply):
    deployed = json.loads((HERE/'deployed.json').read_text())
    client = json.loads((HERE/'client-public-verification.json').read_text())
    wiki = json.loads((HERE/'wiki-publication.json').read_text())
    assert deployed['gateway_open'] and not deployed['database_restored'] and not deployed['cache_changed']
    assert client['release'] == 2026110602 and client['hosted'] and client['changed_assets'] == 3
    assert wiki['result'] == 'PASS' and wiki['files'] == 510
    old = {n: (SKILL/n).read_text(encoding='utf-8') for n in ('client.md','items.md','operations.md','wiki.md','sources.json')}
    new = dict(old)
    client_text = '''## Character Stats and augment descriptions — November6 deployed; native QA open

Main PR410/313d497c; source E:/EQ_Local_Dev/_worktrees/character-stats-bonuses.
docs/releases/character-stats-window-20261106/ owns build, native/runtime tests,
guarded deployment, signed HTTPS/client and public wiki receipts plus exact QA.
Inventory -> Stats automatically shows server mod totals/caps, Shield Block,
strongest Hunt contribution, relative Dodge, item spell-haste/mana-preservation
potential and worn Faerune. No command is required. #augstats remains a fallback
with item/spell/AA block components. Shielding is separate melee reduction.
Focus rows are best worn-item potential before spell/level/cast-time limits;
buff/AA effects can change actual casts. Faerune means worn item utility.

Wire common/equipped_stats_protocol.h [NCST1] has33 ordered int32 fields, existing
five-part UI identity, uint32 sequence and bounded512-byte strict decoding.
Identity/replay/8second expiry guards show -- instead of stale or invented zero.
Class/zone/character lifecycle clears values. Existing Label/Chat/State hooks in
ui_hooks.h service EQTypes10100..10132,10200..10205,10300..10312,10400; no new
native patch sites. client_character_stats_ui.py scopes the current published
Inventory XML, inserts block/Hunt by Shielding and Dodge by Avoidance, keeps two
native columns and provides scrollable focus/utility. Native pixels are not yet
owner accepted. Existing inventory/pet/class controls and unrelated assets stay.

Silent #nightcapui stats requests use existing self-only transport, at most1/sec
while labels render. Server RefreshEquippedStats preserves the existing3second
class-UI throttle and captures actual getters/caps without DB queries, cast RNG
or focus consumption. Permission checks remain; this exact read-only poll bypasses
GM quest callbacks/persistent command logs. Eligible worn items/augs only; no bags
or ordinary slot21 training. Passive focus/worn spell cast level is not an equip
level requirement. Native Client layout/vtable, item ABI and gameplay unchanged.

Signed2026110602/proxy0.13.4 changes DLL, paired catalog and Inventory XML only;
145 descriptors/URLs and signed history/tombstones/config, recall/cast-bar repairs
retained. All148HTTPS hashes/production signature/pair and exact exe preflight
verify. Fully EXIT EQ/use normal launcher Play; relog alone cannot replace DLL.
Protected client untouched. Existing Hunt Description annotation remains, now
pointing to Inventory Stats. Shield requirement/strongest-only text and25 native
Description checks remain. New real hook/protocol/collection/XML tests,14 focused
native/runtime groups,120-site catalog, Go packages and24 Linux fault tests pass.
Owner visible sizing/scroll/refresh and gameplay acceptance remains live QA.
Context topic character-stats pins the reviewed current source and receipts.
'''
    new['client.md'] = section(old['client.md'], '## Hunt augment descriptions — November6 signed client published; native QA open', client_text)
    a = new['items.md'].index('Player #augstats is self-only/read-only:')
    b = new['items.md'].index('\nTests:', a)
    new['items.md'] = new['items.md'][:a] + '''Inventory -> Stats is now the normal equipped-bonus view, automatically refreshed
from paired zone ea6ad532 and signed2026110602/proxy0.13.4. Shield Block/Hunt,
relative Dodge, worn-item focus potential and Faerune have visible rows. Existing
secondary totals/caps come from server getters, including750base damage/healing
and up30earned headroom. #augstats remains the detailed component/stacking fallback.
Numeric copies add within caps; repeated Hunt block/focus/Improved Dodge I/Faerune
do not multiply. Bagged/training items contribute nothing. See client.md and
character-stats topic for wire, refresh, stale-data and native QA boundaries.
''' + new['items.md'][b:]
    new['operations.md'] = section(old['operations.md'], '## Current native baseline — November6 augment Description/report follow-up', f'''## Current native baseline — November6 automatic equipped Stats

Main PR410/313d497c is deployed for owner live QA. Source/worktree:
E:/EQ_Local_Dev/_worktrees/character-stats-bonuses,
docs/releases/character-stats-window-20261106/ owns all immutable receipts and QA.
Zone ea6ad5324fbfd976210d060ad3efd29616c9da53a73f36f5d4fd7cfbd8743d6a;
runtime image {deployed['runtime']['image_id']}. Access reopened after stopped
backup, exact content/rules/cache/all-command-settings guards, saved-state boot
model and expected market rotation. No player snapshot restore or player/item
migration. Worldf33c5925/shared_memory569394cf remain compatible; no new rules,
Client fields/vtable, ItemData or cache ABI. #augstats remains player-access0.

Retained build /tmp/nightcap-character-stats-window-20261106-v3 in local
akk-stack-eqemu-server-1 reproduces live3fc2b901 from144authenticated inputs before
rebuilding only command unity_1 (command.cpp + nightcapui.cpp), preserving the
other11archive members. New common/equipped_stats_protocol.h is a recorded input.
Retains all prior metadata/SSF/Hunt/placeholder/Hate fixes. Do not rebuild from
an older selective/default mirror. New nonvirtual method declaration changes no
native Client ABI. Server must deploy before new signed UI to supply snapshots.

Signed0.13.4/2026110602 DLL/catalog/Inventory XML is published; all148assets verify.
Full EQ exit/launcher Play required. Gameplay and native visible QA remain open.
Whole-runtime child-exit supervision remains: never kill one production zone.
Do not replay terminal jobs. Held rollback uses the compatible prior image; after
opening use a fresh compatible forward repair, never an old player snapshot.

The unrelated dungeon-readiness-20261106 local candidate was built on3fc2b901.
It must reproduce this new ea6ad532 baseline and retain this command archive before
any deployment. Its compiled admission/cache guards remain necessary; operator
contract overrides alone do not alter native Keeper admission. See world.md.
''')
    new['wiki.md'] = section(old['wiki.md'], '## Zone augment audit — November6 published; Description follow-up live QA', '''## Zone augments and character Stats — November6 published; native QA open

Current wiki20261106-character-stats-v1 replaces20261106-augment-description-v1.
All510files/503HTML routes, HTTPS/private-download guards, atomic rollback and
unchanged service identities/start times verify. Five owning guides/Features/
Change Log now direct players to Inventory Stats with automatic server totals,
Shield Block, relative Dodge, worn focus potential/Faerune and real caps/headroom.
#augstats remains diagnostic fallback. Item power/stacking/drops are unchanged;
all item/zone/catalog, Home/navigation, Build Lab and assets are preserved.

Evidence/source E:/EQ_Local_Dev/_worktrees/character-stats-bonuses,
docs/releases/character-stats-window-20261106/{wiki-publication.json,wiki-baseline.json,
wiki-impact.json,test_release_content.py,published-source-overrides.patch}.
Use the exact prior public source plus reviewed scoped delta. Main retains
unrelated source-only previews; never publish it wholesale. Recorded overrides
reproduce actual public source. Historical global source drift remains REVIEW
REQUIRED; no blanket ledger advancement. Paired native ea6ad532 and signed
2026110602/proxy0.13.4 independently verify. Live testing is not owner visual/
gameplay acceptance; native scrolling/sizing/refresh checks remain open.
''')
    manifest = json.loads(old['sources.json'])
    revision = '313d497c479db5b15c3d4fc622abb4625a8aa4ae plus verified release records'
    paths = ['server-mods/code/common/equipped_stats_protocol.h','server-mods/code/zone/gm_commands/nightcapui.cpp',
             'server-mods/code/zone/client.h','server-mods/code/zone/command.cpp','eq-client-dll/src/equipped_stats_state.h',
             'eq-client-dll/src/ui_hooks.h','eq-client-dll/src/ui_state.h','eq-client-dll/src/augment_item_description.h',
             'eq-client-dll/config/patch-sites.json','eq-client-dll/tests/equipped-stats-labels.cpp',
             'tools/client_character_stats_ui.py','tools/client_gameplay_assets.py']
    paths += ['tools/tests/'+n for n in ('test_client_character_stats.py','test_equipped_stats_capture.py','test_equipped_stats_protocol.py')]
    paths += ['docs/releases/character-stats-window-20261106/'+n for n in ('README.md','native-build.json','client-tests.json',
              'rollout.py','deployed.json','client-public-verification.json','wiki-publication.json','wiki-impact.json',
              'test_release_content.py','published-source-overrides.patch')]
    entries = [dict(root=ROOT.as_posix(),path=p,role='Reviewed automatic character Stats release; owner native QA open',
                    revision=revision,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in paths]
    manifest['topics']['character-stats'] = entries
    manifest['observed_revisions']['character_stats_20261106_deployed'] = revision
    for topic in ('items','operations','client','wiki'):
        manifest['topics'][topic] += [e for e in entries if e['path'].endswith(('README.md','deployed.json','client-public-verification.json','wiki-publication.json'))]
    new['sources.json'] = json.dumps(manifest,indent=2)+'\n'
    patch = ''.join(''.join(difflib.unified_diff(old[n].splitlines(True),new[n].splitlines(True),
                    fromfile='a/references/'+n,tofile='b/references/'+n)) for n in new)
    (HERE/'installed-skill-update.patch').write_text(patch,encoding='utf-8')
    if apply:
        for n,text in new.items(): (SKILL/n).write_text(text,encoding='utf-8',newline='\n')
    (HERE/'skill-maintenance.json').write_text(json.dumps(dict(status='applied' if apply else 'prepared',
                     reviewed_entries=len(entries),revision=revision),indent=2)+'\n')
    print('Applied' if apply else 'Prepared', len(entries), 'reviewed release fingerprints')


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true')
    main(parser.parse_args().apply)
