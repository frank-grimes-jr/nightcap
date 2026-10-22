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
at Shakrn Meadowgreen14075 in southkarana -> normal Crafted Gauntlets4178. Five
older soltemple scripts (Gardern/Joyce/Sultin/Vilissia/Vurgo) now delegate their17
recipes to the native helper; reward/EXP/faction values stay. No inventory-ID
normalization or universal reward upgrading. Lua retains trade-slot semantics.

Exact native hand-in/return and task-filter fixtures pass on Windows/Linux; actual
Shakrn Lua and221 Perl assertions pass. Fresh independent review's Vilissia
encoding finding is resolved. Full zone6da991b6 is built over byte-reproduced
deployed5dd5a655 baseline; two implementation objects change, no ABI. Pair zone
with six quest files and supported full-runtime restart, not a zone kill or just
quest reload. No SQL/world/cache/client change; preserve current pair and player
state during recovery. Full task delivery lifecycle remains in-game QA.
Source/tests/manifest/review/recovery/QA: {RELEASE}.
'''
    wiki = f'''{state} Current source: {ROOT.as_posix()}.
All21 guides and432 generated routes reviewed. Equipment, Features, home,
item upgrades, In development and Recent changes carry candidate-only notices
for ordinary quality quest ingredients. Keep quest rewards, explicit quality
requirements and forging rules distinct. Catalog values/commands are unchanged.
Current waypoint/robe guidance is preserved by integration; published ledger
is retained and check_refresh includes actual working changes.14 Python checks,
13 Node scenarios and458-page build pass. No public wiki publication claimed.
Evidence: {RELEASE}wiki-review.json, wiki-refresh.json and QA.md.
'''
    updates = {}
    for name, content in [('world', body), ('items', body), ('wiki', wiki)]:
        path = SKILL / 'references' / (name + '.md')
        before = path.read_text(encoding='utf-8')
        updates[path] = (before, section(before, 'Quest ingredient qualities — October 22 candidate', content))
    source_path = SKILL / 'references/sources.json'
    before = source_path.read_text(encoding='utf-8')
    sources = json.loads(before)
    paths = {
        'world': ['server-mods/code/zone/npc.cpp', 'server-mods/code/zone/task_client_state.cpp',
                  'server-mods/quests/lua_modules/items.lua',
                  *['server-mods/quests/soltemple/' + n + '.pl' for n in ['Gardern','Joyce','Sultin','Vilissia','Vurgo']],
                  'tools/tests/test_quest_handins.py', 'tools/tests/quest_handins.lua', 'tools/tests/quest_handins.t',
                  'tools/tests/fixtures/quest_handins.cpp', 'tools/tests/fixtures/quest_delivery.cpp',
                  'tools/capture_quest_handins.py', RELEASE+'README.md', RELEASE+'QA.md',
                  RELEASE+'verification.json', RELEASE+'review.json', 'docs/status.md', 'CHANGES.md'],
        'items': ['server-mods/code/common/quest_item_policy.h', RELEASE+'native-build-manifest.json',
                  RELEASE+'production-audit.json', 'docs/adr/0066-tiered-quest-ingredients.md'],
        'wiki': ['wiki/articles/'+n+'.json' for n in ['equipment','features','index','item-upgrades','unreleased','recent-changes']]
                + ['wiki/content-review.json', RELEASE+'wiki-review.json', RELEASE+'wiki-refresh.json'],
    }
    if promotion.exists():
        paths['world'].append(RELEASE+'promotion.json')
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
