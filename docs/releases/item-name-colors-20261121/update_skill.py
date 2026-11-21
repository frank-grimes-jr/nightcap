"""Save the exact installed-knowledge patch, optionally install reviewed bytes."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SKILL = Path('C:/Users/verre/.codex/skills/nightcap-development')
SECTION = '''## Item name colors — November 21 published client

Owner-authorized main PR 517 merged at c65d6adc194f946d32d67d1c6be6af8551bd6556.
Signed client 2026112101 / proxy 0.13.7-dev and matching catalog were published and
verified through canonical HTTPS on November 21. Source and release evidence:
E:/EQ_Local_Dev/_worktrees/item-name-colors. Player visual acceptance remains OPEN.
Usable inspection headings, Advanced loot rows/details and Bazaar
seller rows/quotes use Regular green #00FF00, Polished blue #0070DD, Exalted
purple #A335EE and Ascended orange #FF8000; Hunt Ascension is also orange.
Exact suffixes and catalog-bounded dungeon prefixes avoid coloring natural stock
names such as Polished Granite Tomahawk. Native red/unmet-requirement purple and
disabled gray remain. Buttons retain tier colors on hover/press. Ordinary native
chat, merchant/buyer lists and tooltips are separate, unchanged rendering paths.
Source: eq-client-dll/src/item_name_color.h, ui_hooks.h, advanced_loot_{ui,screen}.h
and bazaar_panel_hooks.h. Existing guarded UpdateStrings follows native SetItem;
only the item heading at window+0x314 / label+0x12c changes. Known button hover/
pressed fields are+0x210/+0x214; disabled+0x218 stays native. The protected client
is read-only. Native fixture executes UpdateStrings and CButtonWnd text selection;
font/GPU boundaries are mocked. 51 native color/description and 78 equipment checks,
policy/controller suites, full x86 build and 120-site catalog verification pass.
The published DLL/catalog pair preserves 146 unrelated asset descriptors; the
signed channel verifies against the shipped production key. Fully exit EQ and
launcher Play to install. No server/cache/SQL/reload requirement or runtime restart;
all five services and the newer AA purchase runtime remained unchanged. 20 Linux
client publisher/recovery tests pass. Native fixtures do not establish visible QA.
Evidence, exact player steps, source merge, public receipts and recovery:
docs/releases/item-name-colors-20261121/{README.md,verification.json,
source-merge.json,client-published.json,client-public-verification.json}.

'''
WIKI = '''## Item name colors — November 21 published wiki

Owner-authorized wiki 20261121-item-name-colors-v1 was published over the exact
retained 20261121-aa-purchase-latency-v1 source, preserving 627 of 631 files. Equipment,
Advanced loot and Change Log plus rebuilt search changed. All 631 canonical HTTPS
hashes/security headers and five private-path 404 checks passed at
2026-11-21T14:11:34.806663+00:00. The staged public source is retained under
E:/EQ_Local_Dev/_worktrees/item-name-colors/artifacts/item-name-colors/wiki-release/wiki.
All 44 authored pages, Home/Features/commands and generated item/zone catalog impacts
were reviewed; no numeric/catalog changes. 24 wiki tests, six search cases and 16
Linux publisher tests pass. Rollback rehearsal preserved five services, config
bytes/inode, private downloads and the signed client. Client 2026112101 is published;
player visual acceptance remains OPEN.
Historical source drift stays REVIEW REQUIRED with no unrelated ledger advance.
See docs/releases/item-name-colors-20261121/{wiki-review.json,wiki-publication.json,
wiki-public-verification.json,prepare_wiki.py}.

'''
FILES = ['eq-client-dll/src/item_name_color.h','eq-client-dll/src/ui_hooks.h',
    'eq-client-dll/src/advanced_loot_ui.h','eq-client-dll/src/advanced_loot_screen.h',
    'eq-client-dll/src/bazaar_panel_hooks.h','eq-client-dll/config/patch-sites.json',
    'eq-client-dll/tests/item-name-color.cpp','eq-client-dll/tests/augment-item-window.cpp',
    'eq-client-dll/tests/advanced-loot-controller.cpp','eq-client-dll/tests/bazaar-panel-native.cpp',
    'docs/releases/item-name-colors-20261121/README.md',
    'docs/releases/item-name-colors-20261121/verification.json',
    'docs/releases/item-name-colors-20261121/wiki-review.json',
    'docs/releases/item-name-colors-20261121/source-merge.json',
    'docs/releases/item-name-colors-20261121/client-published.json',
    'docs/releases/item-name-colors-20261121/client-public-verification.json',
    'docs/releases/item-name-colors-20261121/wiki-publication.json',
    'docs/releases/item-name-colors-20261121/wiki-public-verification.json']

def prepend(text, section):
    title = '## Item name colors — November 21 '
    if title in text:
        start = text.index(title)
        end = text.find('\n## ', start+len(title))
        return text[:start] + section + (text[end+1:] if end >= 0 else '')
    first = text.index('\n')+1
    return text[:first] + '\n' + section + text[first:].lstrip('\n')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    paths = ['SKILL.md','references/client.md','references/wiki.md','references/sources.json']
    before = {name:(SKILL/name).read_text(encoding='utf-8') for name in paths}
    after = dict(before)
    route = '| Item name quality colors | [Client and pets](references/client.md) / `item-name-colors` |\n'
    if route not in after['SKILL.md']:
        anchor = '| Heroic stats, yellow totals and Inventory display |'
        after['SKILL.md'] = after['SKILL.md'].replace(anchor,route+anchor)
    after['references/client.md'] = prepend(before['references/client.md'],SECTION)
    after['references/wiki.md'] = prepend(before['references/wiki.md'],WIKI)
    data = json.loads(before['references/sources.json'])
    entries = []
    for path in FILES:
        entries.append({'root':ROOT.as_posix(),'path':path,
            'role':'Reviewed item-name color implementation/test/publication evidence; player visual acceptance OPEN',
            'revision':'main PR 517 c65d6adc; signed client 2026112101 and wiki 20261121-item-name-colors-v1 verified; 2026-11-21 release records',
            'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()})
    by_path = {e['path']:e for e in entries}
    for topic in ('client','wiki'):
        for entry in data['topics'][topic]:
            if entry['path'] in by_path:
                entry.update(by_path[entry['path']])
    data['topics']['item-name-colors'] = entries
    data['observed_revisions']['item_name_colors_20261121'] = 'main PR 517 c65d6adc; client 2026112101/proxy 0.13.7-dev and wiki 20261121-item-name-colors-v1 published and HTTPS verified; five services unchanged; visible QA OPEN'
    after['references/sources.json'] = json.dumps(data,ensure_ascii=False,indent=2)+'\n'
    patch = ''.join(''.join(difflib.unified_diff(before[p].splitlines(True),after[p].splitlines(True),fromfile='a/'+p,tofile='b/'+p)) for p in paths)
    if patch:
        (OUT/'published-skill.patch').write_text(patch,encoding='utf-8')
    staged = OUT/'skill-update'
    for p in paths:
        dest = staged/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(after[p],encoding='utf-8')
    if args.install:
        for p in paths:
            if before[p] != after[p]: (SKILL/p).write_text(after[p],encoding='utf-8')
        (OUT/'published-skill-installation.json').write_text(json.dumps({'status':'installed','files':{
            p:hashlib.sha256((SKILL/p).read_bytes()).hexdigest() for p in paths}},indent=2)+'\n',encoding='utf-8')
    print('Installed reviewed skill update' if args.install else 'Saved exact skill patch and staged validation files')

if __name__ == '__main__':
    main()
