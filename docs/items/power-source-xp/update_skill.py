"""Prepare exact installed-knowledge patches; --apply installs with preimage checks."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
SKILL = Path('C:/Users/verre/.codex/skills/nightcap-development')
OUT = Path(__file__).resolve().parent


def section(text, heading, body):
    start = text.find(heading)
    if start >= 0:
        end = text.find('\n## ', start + len(heading))
        return text[:start] + body + (text[end + 1:] if end >= 0 else '')
    position = text.index('\n## ') + 1
    return text[:position] + body + text[position:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    files = ['SKILL.md', 'references/items.md', 'references/wiki.md', 'references/sources.json']
    before = {n: (SKILL/n).read_text(encoding='utf-8') for n in files}
    after = dict(before)
    heading = '## Power Source item experience — October30 candidate, not released'
    body = heading + '''

Source: E:/EQ_Local_Dev/_worktrees/power-source-item-xp,
feature/power-source-item-xp. Items:PowerSourceItemXP defaults false. Slot21 trains
one complete ordinary or Hunt four-tier family from eligible pre-AA combat XP;
character/AA XP is not spent, and level cap does not prevent progress. Required
and recommended levels apply. No training equipment stats, augments, focus,
worn/click benefits, auto-equip or attunement. Actual Power Sources retain behavior.
Normal/Base -> Polished -> Exalted -> Ascended/Ascension costs80/160/240 comparable
kill equivalents. Owner target4–8hours assumes60–120equivalents/hour; this is a
model, not timed combat acceptance. Current item stats and drop rates are unchanged.

Versioned item-ID-bound progress lives in custom_data, not a GUID side table.
Runtime GUIDs regenerate on login. Exact saved-row UPDATE preserves saved GUID,
charges, binding, compatible augments, grip and explicit dye; default color follows
the successor. Uncertain writes/publication quarantine before stale saves. Native
multi-key loading is repaired in this candidate; old consumers remain unsafe for
XP plus grip. Box/#zoneforge keep3/4/4costs; otherwise eligible partial-XP inputs
are consumed without pooling progress into the output. Player #itemxp reports it.

Sources: common/item_xp_{policy,metadata,inventory,eligibility}.h,
zone/advanced_loot_inventory.cpp, exp.cpp and equipment/packet guards. Tests:
tools/tests/test_item_xp_*.py, actual AA/grip/Bazaar regressions; disposable MariaDB
uses synthetic data. Actual award failure/publication, native slot methods, bonus
dispatch and raw AC checks pass. Thirteen affected translation units compile with
source/object/dependency hashes in native-compile-final.json. Full paired build,
remaining custody/client checks and owner pacing acceptance are separate gates;
consult docs/items/power-source-xp/PLAN.md and QA.md for current evidence.

Pair world/zone/shared_memory and every item-loading consumer: new rules require
matching world, and old metadata loaders are not a safe rollback. Disable the rule
to stop training while retaining metadata and effect suppression. Never restore
old player inventories or replay uncertain writes. RoF2 receives a server-side
slot mask; real signed-client drag/drop still needs QA. No production, protected
client, rule activation or public wiki publication is authorized by this work.

'''
    after['references/items.md'] = section(before['references/items.md'], heading, body)
    old = 'rejected before escrow. Native multi-key custom data cannot roundtrip; posting\nrejects rather than normalizing.'
    new = ('rejected before escrow. The deployed historical loader cannot roundtrip native\n'
           'multi-key custom data; posting rejects rather than normalizing. The separate\n'
           'Power Source XP candidate repairs this loader and tests XP plus grip roundtrips;\n'
           'that is not a claim of a deployed parser update.')
    after['references/items.md'] = after['references/items.md'].replace(old, new)
    wiki_heading = '## Power Source XP — October30 local candidate previews'
    after['references/wiki.md'] = section(before['references/wiki.md'], wiki_heading, wiki_heading + '''

E:/EQ_Local_Dev/_worktrees/power-source-item-xp has Not released previews in
Item upgrades, Equipment, Zone Hunt, Commands, Features, In development and
Change Log. All40authored articles and generated catalog impacts are assessed in
docs/items/power-source-xp/wiki-review.json. No catalog stats, drops or existing
recipes change. Home keeps compact goal paths; no release announcement is added.
All19wiki/refresh checks pass using workspace TEMP/TMP. The historical global
ledger still reports unrelated drift and is not blanket-advanced. No publication
is claimed. Preserve newer Hate-density and other public October30 changes when
preparing any eventual publication; this candidate checkout is not that authority.

''')
    row = '| Power Source item XP candidate | [Items and economy](references/items.md) / `item-xp` |\n'
    if row not in after['SKILL.md']:
        marker = '| Tradeskills, loot tiers, augments, upgrades, trade/LORE, sell-all | [Items and economy](references/items.md) / `items` |\n'
        assert marker in after['SKILL.md']
        after['SKILL.md'] = after['SKILL.md'].replace(marker, marker + row)
    manifest = json.loads(before['references/sources.json'])
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() + ' plus reviewed candidate working tree; not deployed'
    paths = sorted({
        *[p.relative_to(ROOT).as_posix() for p in (ROOT/'tools/tests').glob('test_item_xp_*.py')],
        *['server-mods/code/' + n for n in __import__('runpy').run_path(str(ROOT/'tools/build_item_xp.py'))['FILES']],
        'tools/tests/fixtures/item_xp_award.cpp', 'tools/tests/test_bazaar_native.py',
        'tools/tests/test_paladin_weapon_grip.py', 'tools/tests/test_passive_aa.py',
        'docs/items/power-source-xp/QA.md', 'docs/items/power-source-xp/PLAN.md',
        'docs/items/power-source-xp/calibration.json', 'docs/items/power-source-xp/native-compile-final.json',
        'docs/items/power-source-xp/wiki-review.json', 'docs/adr/0073-power-source-item-experience.md',
    })
    manifest['topics']['item-xp'] = [dict(root=ROOT.as_posix(), path=n, revision=revision,
        role='Reviewed Power Source XP candidate implementation/test/evidence; not deployed or owner accepted',
        sha256=hashlib.sha256((ROOT/n).read_bytes()).hexdigest()) for n in paths]
    after['references/sources.json'] = json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'
    patch = ''.join(''.join(difflib.unified_diff(before[n].splitlines(True), after[n].splitlines(True),
                    fromfile='a/'+n, tofile='b/'+n)) for n in files)
    (OUT/'installed-skill.patch').write_text(patch, encoding='utf-8')
    if args.apply:
        for n in files:
            assert (SKILL/n).read_text(encoding='utf-8') == before[n], 'Concurrent skill edit: '+n
        for n in files:
            if before[n] != after[n]:
                (SKILL/n).write_text(after[n], encoding='utf-8')
    print('Installed reviewed candidate knowledge' if args.apply else 'Exact installed-skill.patch prepared; not installed')


if __name__ == '__main__':
    main()
