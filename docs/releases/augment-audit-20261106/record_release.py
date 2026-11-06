"""One-shot reconciliation of verified public source and release evidence."""
import difflib
import json
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PUBLIC = ROOT / 'artifacts/augment-audit-release/wiki-source/wiki'
WIKI = ROOT / 'wiki'


def section(body, anchor):
    match = re.search(r'<h([23]) id="' + re.escape(anchor) + r'">', body)
    assert match, anchor
    end = re.search(r'<h[1-' + match[1] + r']\b|<p class="notice" id="augment-audit-preview"', body[match.end():])
    return body[match.start():match.end() + end.start() if end else len(body)]


preserve = {
    'zone-hunt': ['power-source-training'],
    'equipment': ['power-source-training'],
    'features': ['power-source-training', 'faction-standings-preview'],
    'recent-changes': ['power-source-training-20261030', 'faction-standings-main-20261030'],
}
names = ['zone-hunt', 'equipment', 'features', 'camil-vigil', 'ashen-compact',
         'recent-changes', 'zone-kael', 'augment-audit']
for name in names:
    path = WIKI / 'articles' / (name + '.json')
    old = json.loads(path.read_text(encoding='utf-8'))
    new = json.loads((PUBLIC / 'articles' / path.name).read_text(encoding='utf-8'))
    for anchor in preserve.get(name, []):
        new['body'] += '\n' + section(old['body'], anchor)
    path.write_text(json.dumps(new, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for name in ['catalog.json', 'catalog.py', 'chapterhouse_catalog.py']:
    shutil.copy2(PUBLIC / name, WIKI / name)
for path in (PUBLIC / 'articles').glob('item-96102*.json'):
    shutil.copy2(path, WIKI / 'articles' / path.name)
p = WIKI / 'build.py'
s = p.read_text(encoding='utf-8').replace('384 rewards grouped into 96 item families', '392 rewards grouped into 98 item families')
p.write_text(s, encoding='utf-8')
p = WIKI / 'augment-candidate.json'
d = json.loads(p.read_text()); d['status'] = 'Live testing'
p.write_text(json.dumps(d, indent=2) + '\n')
p = WIKI / 'augment_candidate.py'
s = p.read_text().replace("    ids = {", "    if preview['status'] != 'Not released':\n        return articles\n    ids = {")
p.write_text(s)

# Exact publication source remains reproducible even where main has unrelated
# source-only previews. These overrides are evidence, not another publication.
diff = []
for path in sorted(PUBLIC.rglob('*')):
    rel = path.relative_to(PUBLIC)
    if not path.is_file() or rel.parts[0] in ('dist', '__pycache__') or path.suffix not in ('.py', '.json', '.css', '.js', '.svg', '.html', '.txt'):
        continue
    base = WIKI / rel
    before = base.read_text(encoding='utf-8') if base.exists() else ''
    after = path.read_text(encoding='utf-8')
    if before != after:
        diff.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                    fromfile='a/wiki/' + rel.as_posix(), tofile='b/wiki/' + rel.as_posix()))
(HERE / 'published-source-overrides.patch').write_text(''.join(diff), encoding='utf-8')

release = '''**Deployed on OVH for live QA, November 6.** Owner-authorized main PR
[#406](https://github.com/frank-grimes-jr/nightcap/pull/406) merged as
`3a0cb2d36d14b0ec6dead3ff44c0b98df3ab5f65`. Player access is open.
The 232 item afterimages, two zone-enable flags, native identities and regenerated
item cache are verified. Fifty Classic pools and both managed expeditions now
roll augments at 1.5%; six dormant pools stay disabled. All other item definitions
are preserved. Icon artwork is accepted; gameplay/balance acceptance is pending.
No client download is required; fully relog before item QA. The unrelated capacity
candidate was excluded. [Release evidence](../../releases/augment-audit-20261106/README.md).
'''
p = ROOT / 'docs/audits/augments-20261106/README.md'
s = p.read_text(encoding='utf-8'); start = s.index('**Candidate only.'); end = s.index('\nThe [complete', start)
s = s[:start] + release + s[end:]; p.write_text(s, encoding='utf-8')
p = ROOT / 'docs/audits/augments-20261106/AUGMENTS.md'
s = p.read_text(encoding='utf-8'); i = s.index('\n')
s = s[:i] + '\n\nLive release: see [deployment evidence](../../releases/augment-audit-20261106/README.md). The table preserves the original audit capture; Cazic-Thule and Hate B are now enabled and both expedition rates are now 1.5%. Six other disabled pools remain off.\n' + s[i:]
p.write_text(s, encoding='utf-8')
p = ROOT / 'CHANGES.md'; s = p.read_text(encoding='utf-8')
s = s.replace('# CHANGES\n', '''# CHANGES

## 2026-11-06 — Augments deployed to OVH for live QA

Owner-authorized augment-only main PR #406 is deployed; access reopened after
verified stopped backup, guarded SQL, compatible zone image and cache checks.
All 232 item definitions match; 309,639 unrelated cached definitions are unchanged.
Fifty Classic and two expedition pools roll augments at 1.5%, including unowned
killable guards/adds. Two reviewed zones enabled; six dormant pools remain off.
The accepted gem/crystal icons require no client download. Fully relog for QA.
Public wiki release `20261106-augment-audit-v2` verified all 510 files, rollback,
private downloads and unchanged service identities. Gameplay acceptance remains
open; separate capacity changes were excluded. Evidence and exact QA:
`docs/releases/augment-audit-20261106/`.
''', 1); p.write_text(s, encoding='utf-8')
p = ROOT / 'docs/status.md'; s = p.read_text(encoding='utf-8')
start = s.index('## November 6'); end = s.index('\n## Power Source', start)
s = s[:start] + '''## November 6 — Augments deployed; live QA open

Owner-approved augment-only main PR #406 is deployed on OVH; player access is open.
All 232 item updates, zone 48/186 enables, matching native image and shared cache
passed verification. All 309,639 unrelated cache definitions were preserved.
Fifty Classic pools and both expeditions now use 1.5% augment rolls for any
unowned killable NPC, including guards and scripted adds; six dormant pools stay
disabled. Gear eligibility remains separate. Accepted exotic icons use stock
client assets: no download required, fully relog before testing.

Wiki release `20261106-augment-audit-v2` passed full 510-file public verification
and rollback rehearsal. [Full augment list](https://wiki.nightcapgame.org/augment-audit.html),
[release receipts and live QA steps](releases/augment-audit-20261106/README.md).
Artwork accepted; gameplay/balance acceptance remains open. Separate capacity
configuration was excluded. Existing world/shared_memory and signed client retained.
''' + s[end:]; p.write_text(s, encoding='utf-8')
p = HERE / 'README.md'; s = p.read_text(encoding='utf-8')
s += '''
## Verified completion

Main PR #406 merged as `3a0cb2d36d14b0ec6dead3ff44c0b98df3ab5f65`.
`deployed.json` is the independently fetched, authenticated host receipt after
preflight, activation and access reopening all terminated successfully.
The stopped backup passed gzip verification (66,424,213 compressed bytes;
SHA256 `6579b762149c0a0b3af8b91a70f42d73dc680a2e36797e7f4c8c7779d999b6dd`).
The item loader contains 309,871 definitions: exactly 232 changed and 309,639
unrelated definitions preserved. No player restore or client release occurred.

`wiki-publication.json` records verified HTTPS publication of 510 files under
`20261106-augment-audit-v2`, replacing `20261101-hunt-rates-v1`. Linux publication
and recovery tests passed; pointer rollback was rehearsed. Private downloads,
nginx configuration and all service image/start identities were preserved.
The actual prior public source was reproduced byte-for-byte before editing;
the published source is main's wiki plus `published-source-overrides.patch`.
That scoped evidence patch preserves the distinction between public source and
unrelated source-only previews; do not blindly publish main's entire wiki.
`test_wiki_release.py` verifies every generated link/anchor, actual afterimages,
new augment-only zones, unchanged ordinary gear and unchanged Build Lab model.
`wiki/check_refresh.py` still reports historical source drift; the global ledger
was not blindly advanced. The entire public guide/catalog impact was reviewed.

**Owner artwork acceptance is recorded; gameplay/solo balance acceptance remains
open.** Run the audit README's nine-part QA, including the named guards, High Keep
rescue adds, daytime Kithicor, CT/Hate B, both expeditions and specialty stacking.
'''; p.write_text(s, encoding='utf-8')
print('Recorded verified release; preserved unrelated source-only preview sections.')
