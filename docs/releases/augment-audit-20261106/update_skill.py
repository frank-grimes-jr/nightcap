"""Prepare/apply reviewed deployed-state knowledge; writes installation only with --apply."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SKILL = Path('C:/Users/verre/.codex/skills/nightcap-development/references')


def replace_section(text, heading, replacement):
    start = text.index(heading)
    end = text.index('\n## ', start + len(heading))
    return text[:start] + replacement.rstrip() + '\n' + text[end:]


def main(apply):
    old = {n: (SKILL / n).read_text(encoding='utf-8') for n in ('items.md', 'operations.md', 'wiki.md', 'sources.json')}
    new = dict(old)
    items = old['items.md']
    start = items.index('## Zone augment audit — November6 candidate, not deployed')
    end = items.index('\n## ', start + 5)
    section = items[start:end]
    section = section.replace('candidate, not deployed', 'deployed for live QA').replace('reviewed e13a307de5700270ab250e6d1d7d2544d16746d4.', 'main PR406/3a0cb2d36d14b0ec6dead3ff44c0b98df3ab5f65.').replace('Fresh read-only production capture:48Classic\npools at1.5%, eight disabled, two managed expeditions at0.5%;58families/232augments.', 'Live November6:50Classic pools and two managed expeditions at1.5%; six dormant\npools remain disabled.58families/232augments; all232definitions verified.').replace("this reviewed candidate's", "this reviewed release's").replace('Candidate augments roll', 'Live augments roll')
    cut = section.index('Evidence/full58-item list/icons/QA/runbook:')
    section = section[:cut] + '''Evidence/full58-item list/icons/nine-part guard/add/expedition/stacking/solo QA:
docs/audits/augments-20261106/ and docs/releases/augment-audit-20261106/.
Owner explicitly accepted icon artwork and authorized main/OVH for live QA.
Main PR406 uses the augment-only main-based branch; unrelated capacity candidate
on dev/test was excluded. Preflight/activation/open all succeeded, then a fresh
readback verified native/cache/content and reopened gateway.232afterimages and
two enable flags match;309639unrelated cache definitions preserved. Stopped backup
gzip verified; no player snapshot restored. Public wiki510files verified.
Gameplay/solo balance acceptance remains open. Named guards: High Keep Heltch6000,
Golgon6001; Qeynos Hills Yalroen4048. Fully relog for item QA; no client download.
Existing metadata-aware world/shared_memory and signed client retained. Cache
regeneration and supported whole-runtime restart are required; quest/rule reload
is insufficient. Do not replay completed activation or roll back player state.
Post-open repairs need fresh compatible forward plans, never old snapshots or
pre-Power-Source-XP binaries. Missing historical client-archive fixture is not
client acceptance; this release uses existing stock artwork only.
'''
    new['items.md'] = items[:start] + section + items[end:]
    new['items.md'] = new['items.md'].replace('Two independent 0.5% rolls per eligible death: augment and wearable; weights 60/30/8/2, top tier **Ascension**. 48 audited combat zones enabled, eight access-check zones gated.', 'November6: augment1.5% from any unowned killable NPC in50enabled Classic pools; separate0.5% equipment roll keeps its source/level/night gates. Six pools disabled; weights60/30/8/2, top tier **Ascension**. See current augment section; older release is historical.')
    new['operations.md'] = replace_section(old['operations.md'], '## Current native baseline — November4 Power Source training display', '''## Current native baseline — November6 augments deployed for live QA

Owner-authorized main PR406/3a0cb2d3 deployed on OVH November6; gateway reopened.
Evidence: docs/releases/augment-audit-20261106/{deployed.json,README.md} in
E:/EQ_Local_Dev/_worktrees/augment-audit-20261106. Zone SHA256:
bc88a4688d722c89f882ddb3328cf0d26867781fea49199ef681abe4f6c51892.
Runtime image sha256:d885c60cda98602744f1ffe0fa0ad0fd4bf151742afc6b8bdaec66a267626d60.
Existing compatible worldf33c5925/shared_memory569394cf and signed client retained.
The232item updates/two enable flags/cache passed exact afterimage and unrelated
preservation checks. Stopped backup gzip verified; no player data restoration.
Preflight/activate/open jobs all terminal success: never replay activation.

Build first reproduced the November4 zone335cbce1 byte-for-byte from144retained
link inputs, then applied four compiled TUs. Retained baseline source:
/tmp/nightcap-power-source-xp-display-20261103-v1 in akk-stack-eqemu-server-1;
new link artifacts /tmp/nightcap-augment-audit-20261106-v2/link-debug-v1.
Preserve the already-live Hate spawn-source join correction absent from main's
selective mirror. Use retained CMake flags/PCH, strip --strip-debug and runtime
ELF identity verification. Do not start future builds from an older default mirror.
Power Source metadata, SSF, per-zone rates and placeholder-loot repair remain.
No client download; fully relog for item definitions. Artwork accepted; gameplay
and solo balance acceptance remain open. Unrelated capacity changes excluded.
Production child exits restart the whole runtime; use supported whole-runtime
maintenance for this native/cache pairing. Never restore old player snapshots.
''')
    new['wiki.md'] = replace_section(old['wiki.md'], '## Zone augment audit — November6 unpublished preview', '''## Zone augment audit — November6 published for live QA

Owner-authorized main PR406/3a0cb2d3 and verified OVH activation precede publication.
Public release20261106-augment-audit-v2 replaces20261101-hunt-rates-v1; all510files,
HTTPS/private-download guards, atomic rollback and service image/start identities
verified.503HTML pages; unchanged client/art assets. No nginx reload required.
Evidence: docs/releases/augment-audit-20261106/wiki-publication.json, wiki-baseline.json,
test_wiki_release.py and published-source-overrides.patch in the augment worktree.
The actual public baseline was reproduced499files byte-for-byte before editing.
Main retains unrelated source-only previews; exact published source is main's
wiki with the recorded overrides. Never blindly publish an older or main mirror.

Whole41authored-guide plus generated-page review: owning guides, Features,
equipment/catalog, expedition item/zone pages, Change Log and full58family list
updated.50Classic zones/392variants/98families; CT/Hate B have augments only,
no invented gear. All232authored augments updated; six dormant pools documented
but excluded from enabled catalog. Homepage counts/Build Lab item projection
follow the verified catalog; ordinary gear, Build Lab model/spells, assets,
commands and other mechanics unchanged. Exact published links/anchors pass.
Status is Live testing; icon artwork accepted, gameplay/solo QA remains open.
No client update. Historical global source drift remains REVIEW REQUIRED;
no blanket advancement of the old ledger. Other source-only previews retained.
''')
    manifest = json.loads(old['sources.json'])
    revision = '3a0cb2d36d14b0ec6dead3ff44c0b98df3ab5f65 plus reviewed deployment/wiki records'
    manifest['observed_revisions']['augment_audit_20261106_deployed'] = revision
    entries = []
    paths = [e['path'] for e in manifest['topics']['augment-audit']]
    paths += ['docs/releases/augment-audit-20261106/' + n for n in
              ['README.md', 'rollout.py', 'deployed.json', 'wiki-publication.json', 'test_wiki_release.py', 'published-source-overrides.patch']]
    paths += ['wiki/catalog.json', 'wiki/catalog.py', 'wiki/chapterhouse_catalog.py']
    for p in paths:
        entries.append(dict(root=ROOT.as_posix(), path=p, role='Reviewed November6 deployed augment release; artwork accepted, gameplay QA open', revision=revision, sha256=hashlib.sha256((ROOT / p).read_bytes()).hexdigest()))
    manifest['topics']['augment-audit'] = entries
    bypath = {e['path']: e for e in entries}
    for topic in ['items', 'operations', 'wiki']:
        manifest['topics'][topic] = [bypath.get(e['path'], e) if e.get('root') == ROOT.as_posix() else e for e in manifest['topics'][topic]]
    for topic in ['operations', 'wiki']:
        present = {(e['root'], e['path']) for e in manifest['topics'][topic]}
        manifest['topics'][topic] += [e for e in entries if e['path'].startswith('docs/releases/') and (e['root'], e['path']) not in present]
    new['sources.json'] = json.dumps(manifest, indent=2) + '\n'
    patch = ''.join(''.join(difflib.unified_diff(old[n].splitlines(True), new[n].splitlines(True), fromfile='a/references/' + n, tofile='b/references/' + n)) for n in new)
    (HERE / 'installed-skill-deployed.patch').write_text(patch, encoding='utf-8')
    if apply:
        for n, text in new.items():
            (SKILL / n).write_text(text, encoding='utf-8', newline='\n')
    report = dict(status='applied' if apply else 'prepared', reviewed_entries=len(entries), revision=revision)
    (HERE / 'skill-maintenance.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--apply', action='store_true')
    main(parser.parse_args().apply)
