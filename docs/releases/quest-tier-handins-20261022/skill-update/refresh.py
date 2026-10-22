"""Prepare an exact, scoped installed-skill patch; --apply installs reviewed bytes."""
import argparse
import difflib
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SKILL = Path('C:/Users/verre/.codex/skills/nightcap-development')
RELEASE = 'docs/releases/quest-tier-handins-20261022/'


def section(text, title, body):
    marker = '## ' + title + '\n'
    if marker in text:
        start = text.index(marker)
        end = text.find('\n## ', start + len(marker))
        if end < 0:
            end = len(text)
        return text[:start] + marker + '\n' + body.strip() + '\n' + text[end:]
    first = text.index('\n') + 1
    return text[:first] + '\n' + marker + '\n' + body.strip() + '\n' + text[first:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    promotion = ROOT / RELEASE / 'promotion.json'
    state = 'Tested candidate; main/production/player QA remain pending.'
    if promotion.exists():
        state = 'Promoted through dev/test; main/production/player QA remain pending. See promotion.json.'
    body = f'''Source: {ROOT.as_posix()}, reviewed {revision[:12]}.
{state}
Normal quest requirements accept verified ordinary +200000/+400000/+600000
Polished/Exalted/Ascended definitions with exact generated names. Shared Lua
lua_modules/items.lua, native NPC::CheckHandin and task Deliver use this policy;
explicit quality requests, +800000 epics, hunt/dungeon catalogs and forging costs
stay exact. Prefer exact inputs and reserve explicit qualities first; real item
IDs/instances are retained. Failed native money/ingredient/unknown-ID checks
restore counts. Multiquest completion still clears the whole donation bucket,
including surplus; this change does not make extra donations refundable.

Production audit confirms Aviak Charm13737/213737/413737/613737, two Star Rubies10032
at Shakrn Meadowgreen14075 in southkarana. Captured live quest grants4178; the
integrated class-armor candidate grants604178. Both pass all four charm tiers;
the ingredient fix preserves whichever reward policy the quest defines. Five
older soltemple scripts (Gardern/Joyce/Sultin/Vilissia/Vurgo) now delegate their17
recipes to the native helper; reward/EXP/faction values stay. Kurron declares actual coins to native matching and refunds them once on
success, preserving the reviewed no-new-sink policy; failures use native returns.
No inventory-ID
normalization or universal reward upgrading. Lua retains trade-slot semantics.

Exact native hand-in/return and task-filter fixtures pass on Windows/Linux; actual
Shakrn Lua and legacy/Kurron Perl controls pass. Fresh independent review's Vilissia
encoding finding is resolved. Full zone6da991b6 is built over byte-reproduced
deployed5dd5a655 baseline; two implementation objects change, no ABI. Pair zone
with seven quest files and supported full-runtime restart, not a zone kill or just
quest reload. No SQL/world/cache/client change; preserve current pair and player
state during recovery. Full task delivery lifecycle remains in-game QA.
Source/tests/manifest/review/recovery/QA: {RELEASE}.
'''
    wiki = f'''{state} Current source: {ROOT.as_posix()}.
All21 guides and432 generated routes reviewed. Equipment, Features, home,
item upgrades, In development and Recent changes carry candidate-only notices
for ordinary quality quest ingredients. Keep quest rewards, explicit quality
requirements and forging rules distinct. Catalog values/commands are unchanged.
Published waypoint/robe guidance and separate class-armor candidate are preserved;
published ledger
is retained and check_refresh includes actual working changes.14 Python checks,
13 Node scenarios and458-page build pass. No public wiki publication claimed.
Evidence: {RELEASE}wiki-review.json, wiki-refresh.json and QA.md.
'''
    updates = {}
    for name, content in [('world', body), ('items', body), ('wiki', wiki)]:
        path = SKILL / 'references' / (name + '.md')
        before = path.read_text(encoding='utf-8')
        after = section(before, 'Quest ingredient qualities — October 22 candidate', content)
        if name == 'items':
            after = section(after, 'Substantial class-armor rewards — October 22 candidate, not deployed', f'''
The owner permits substantial repeatable class-armor quests; cheap/basic hand-ins
stay excluded. The audited catalog grants existing +600000 Ascended definitions
for37 Crafted/Lambent/Darkforge/Ivy Etched/Totemic terminal rewards. Membership
is docs/items/quest-armor-catalog.json; no new stats, sockets or eligibility.
Other quests, basic crafts, intermediates and epic+800000 stay separate. Armor
of Ro and mixed cleric branches require their own audit; never globally hook
SummonItem/QuestReward. Owned Palwar items need separate authorized correction.

Integrated source: {ROOT.as_posix()} at {revision[:12]}. Kurron requires three
Darkforge pieces and raw platinum>=900. Native matching accepts all four ordinary
qualities. Declare all submitted denominations to CheckHandin, then refund once
on success; failure uses native returns. Preserve faction and one letter/spawn.
This corrects a real currency mismatch; unused quests/plugins/ fixture success
was not evidence of active live behavior. Root plugins/ is configured instead.

All113 armor Lua cases use the current helper.39 historical Perl subtests remain
reward-delta controls; compiled native and357 callback assertions cover integrated
qualities/returns/currency.21 catalog guards pass. Combined activation needs the
paired zone and17 distinct quest/helper files, fresh preimages/cache preflight,
supported full-runtime restart, and authorized wiki publication. No SQL/world/
client/cache replacement. Preserve earned rewards on recovery. {state}
Evidence: docs/releases/quest-armor-20261022/ and {RELEASE}.
''')
        if name == 'wiki':
            after = section(after, 'Class-armor reward candidate — October 22, not published', f'''
The37-reward/five-family candidate stays Not released. Substantial repeatable
class armor qualifies for audit; cheap/basic hand-ins do not. Integrated tier
acceptance and Kurron currency correction are documented separately from reward
selection. All21 guides/432 generated routes were reviewed; current published
waypoint/robe guidance and the publication ledger stay intact. No item catalog
values, commands, owned inventory or public release changed in this task.
Current integrated source: {ROOT.as_posix()} at {revision[:12]}.
Evidence: docs/releases/quest-armor-20261022/ and {RELEASE}wiki-review.json.
Pair future publication with the authorized combined native/quest release.
{state}
''')
        updates[path] = (before, after)
    source_path = SKILL / 'references/sources.json'
    before = source_path.read_text(encoding='utf-8')
    sources = json.loads(before)
    paths = {
        'world': ['server-mods/code/zone/npc.cpp', 'server-mods/code/zone/task_client_state.cpp',
                  'server-mods/quests/lua_modules/items.lua',
                  *['server-mods/quests/soltemple/' + n + '.pl' for n in ['Gardern','Joyce','Sultin','Vilissia','Vurgo']],
                  'tools/tests/test_quest_handins.py', 'tools/tests/quest_handins.lua', 'tools/tests/quest_handins.t',
                  'tools/tests/fixtures/quest_handins.cpp', 'tools/tests/fixtures/quest_delivery.cpp',
                  'server-mods/quests/overthere/Kurron_Ni.pl', 'docs/items/quest-armor-catalog.json',
                  'tools/tests/quest_armor_rewards.t', 'tools/quest_armor.py',
                  'docs/releases/quest-armor-20261022/README.md', 'docs/releases/quest-armor-20261022/QA.md',
                  'docs/releases/quest-armor-20261022/manifest.json',
                  RELEASE+'currency-mutation.json', RELEASE+'integrated-native-source-proof.json',
                  RELEASE+'plugin-path-probe.json', 'tools/capture_quest_handins.py', RELEASE+'README.md', RELEASE+'QA.md',
                  RELEASE+'verification.json', RELEASE+'review.json', 'docs/status.md', 'CHANGES.md'],
        'items': ['server-mods/code/common/quest_item_policy.h', RELEASE+'native-build-manifest.json',
                  RELEASE+'production-audit.json', 'docs/adr/0067-tiered-quest-ingredients.md'],
        'wiki': ['wiki/articles/'+n+'.json' for n in ['equipment','features','index','item-upgrades','unreleased','recent-changes']]
                + ['wiki/content-review.json', RELEASE+'wiki-review.json', RELEASE+'wiki-refresh.json'],
    }
    if promotion.exists():
        paths['world'].append(RELEASE+'promotion.json')
    # Retain other concurrent candidates and dated deployed evidence. Supersede
    # only the reviewed class-armor entries whose files changed in this integration.
    changed = {p for files in paths.values() for p in files}
    for entries in sources['topics'].values():
        for entry in entries:
            if entry['root'].endswith('/quest-armor-ascended') and entry['path'] in changed:
                entry.update(root=ROOT.as_posix(), revision=revision,
                             sha256=hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest(),
                             role='Reviewed class-armor/ingredient integration; candidate, not deployed')
    scoped = {'schema_version': sources['schema_version'], 'audited_at': '2026-10-22', 'topics': {}}
    for topic, files in paths.items():
        entries = [{'root': ROOT.as_posix(), 'path': p, 'role': 'quest ingredient candidate; built/tested, not deployed',
                    'revision': revision, 'sha256': hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in files]
        sources['topics'][topic] = [e for e in sources['topics'][topic]
                                   if not (e['root'] == ROOT.as_posix() and e['path'] in files)] + entries
        scoped['topics'][topic] = entries
    sources['observed_revisions']['quest_tier_handins_20261022'] = revision
    updates[source_path] = (before, json.dumps(sources, ensure_ascii=False, indent=2)+'\n')
    patch = ''.join(''.join(difflib.unified_diff(a.splitlines(True), b.splitlines(True),
                    fromfile=p.as_posix(), tofile=p.as_posix())) for p, (a,b) in updates.items())
    (HERE/'knowledge.patch').write_text(patch, encoding='utf-8', newline='\n')
    (HERE/'scoped-fingerprints.json').write_text(json.dumps(scoped, indent=2)+'\n', encoding='utf-8')
    if args.apply:
        for path, (old, new) in updates.items():
            if path.read_text(encoding='utf-8') != old:
                raise RuntimeError('Installed skill changed during preparation: '+str(path))
            path.write_text(new, encoding='utf-8', newline='\n')
    (HERE/'receipt.json').write_text(json.dumps({'status': 'installed' if args.apply else 'prepared_pending',
        'revision': revision, 'files': {p.as_posix():hashlib.sha256(b.encode()).hexdigest() for p,(a,b) in updates.items()}}, indent=2)+'\n')
    print('Installed' if args.apply else 'Prepared', len(updates), 'scoped skill files')


if __name__ == '__main__':
    main()
