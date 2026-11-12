"""Prepare an exact installed Nightcap knowledge patch; --apply checks preimages."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/items/augment-icons-20261112'
SKILL = Path('C:/Users/verre/.codex/skills/nightcap-development')
HEADING = '## Stat augment icons'


def deployed_section():
    live = json.loads((OUT / 'production-verification.json').read_text(encoding='utf-8'))
    wiki = json.loads((OUT / 'wiki-public-verification.json').read_text(encoding='utf-8'))
    build = json.loads((OUT / 'native-build.json').read_text(encoding='utf-8'))
    assert live['status'] == wiki['status'] == build['status'] == 'PASS'
    zone = build['shipping']['candidate-zone'][:8]
    return f"""## Stat augment icons — November 12 deployed for visual QA

Main PR420/1568fb71, source00ee567f, worktree
E:/EQ_Local_Dev/_worktrees/augment-item-icons. Paired native zone{zone},
world{build['shipping']['candidate-world'][:8]} and
shared_memory{build['shipping']['candidate-shared_memory'][:8]} are deployed;
admissions reopened. docs/items/augment-icons-20261112/ owns release/repair proof.
Ordinary stat augments no longer count as ornaments through empty/ordinary
IDFile. AugType uses bits for socket20/21; explicit Hero's Forge fallback remains.
Packet handlers recalculate cosmetics only when the old target or Insert/Swap
cursor is a real ornament, captured before callbacks/mutation. Stat-only insert,
remove, swap and destroy preserve genuine mold/quest overrides; unrelated cursor
ornaments cannot influence Remove/Destroy. Native method/caller regressions in
tools/tests/test_augment_ornament_native.py + fixtures/augment_ornament.cpp.

Three shipping binaries first reproduce exactly; isolated two-file transplant,
three compiles/relinks, ELF loaded-byte identity and182actual dependencies
including179authenticated source headers pass.17focused regressions and actual
MariaDB rollback/drift/five-field-forward/replay controls pass. Independent review
findings about explicit cosmetics and post-open campaign activity are resolved;
owner declined an additional cross-model review. No client download, definitions,
rule, schema, ItemData or cache-format change. Keep current metadata-aware native
pair, unchanged cache/quests/signed client and newer Last Lantern systems.

Owner-authorized Palwar repair changes ornament_icon only in five confirmed
worn rows. Current Hunt icons plus historical Understone517afterimages explain
them; no genuine ornament, base/saved HF or model override was present. Exact
SQL-side full-row preimage locks/afterimage guards preserve all205inventory rows,
augments, charges, dye, binding, custom data, GUID and unrelated inventory. Fresh
stopped full backup, GM/deploy locks, zero clients,125secondauth drain, supported
whole-runtime stop/restart, normal saved-state/one-market-rotation checks and
native/service identities verify. No player snapshot restore. Do not replay a
terminal action or bulk-clear cosmetics; future incidents need fresh scoped rows.

Preexisting HF raw-save/load defects are separate: naive loading of the saved
hero field can repeatedly expand shorthand values. Do not fold a global HF
migration into icon repair; the repaired rows have zero HF and all other fields
are verified unchanged. Source: shareddb.cpp save/load and GetOrnamentHeroModel.

Wiki20261112-augment-icons-v1 publishes five owning/status/history guides plus
search;607of613files retained. Exact previous public source reproduced; all613
canonical HTTPS hashes/security headers and five private denials pass, publisher
rollback rehearsed, all five service identities retained. No global source-ledger
advance. Owner in-game icon/model/stat/persistence acceptance remains OPEN.
"""


def replace_section(text, prefix, replacement):
    if prefix in text:
        start = text.index(prefix)
        end = text.find('\n## ', start + len(prefix))
        return text[:start] + replacement.rstrip() + '\n' + (text[end:] if end >= 0 else '')
    title_end = text.index('\n') + 1
    return text[:title_end] + '\n' + replacement.rstrip() + '\n\n' + text[title_end:].lstrip('\n')



def main(apply):
    originals = {name: (SKILL / 'references' / name).read_text(encoding='utf-8')
                 for name in ('items.md', 'operations.md', 'wiki.md', 'sources.json')}
    section = deployed_section()
    updated = {'items.md': replace_section(originals['items.md'], HEADING, section)}
    updated['operations.md'] = replace_section(originals['operations.md'], '## Current native baseline', section.replace('## Stat augment icons — November 12 deployed for visual QA', '## Current native baseline — November 12 augment icons'))
    updated['wiki.md'] = replace_section(originals['wiki.md'], '## Augment icon correction', """## Augment icon correction — November 12 published

Wiki20261112-augment-icons-v1 follows owner-authorized main PR420/native activation.
All613previous files reproduced from authenticated published source before six
changed outputs: Equipment, Zone hunt, augment audit, In development, Change Log
and search.607files remain exact; no Home/Features/command/catalog values change.
All42authored articles and generated projections reviewed. All613HTTPS hashes,
security headers and five private denials pass; pointer rollback rehearsed,
private downloads/config and five service identities retained. No Nginx reload.
Player visual/gameplay acceptance stays open; published is not accepted. Global
historical source drift stays REVIEW REQUIRED; no blind ledger advance.
Source/reproduction/verification: E:/EQ_Local_Dev/_worktrees/augment-item-icons,
docs/items/augment-icons-20261112/ and tools/prepare_augment_icon_wiki.py.
No raw player rows/backups/repair SQL enter the public artifact. Preserve the
Last Lantern613-file catalog/reward projections and unrelated released content.
""")
    manifest = json.loads(originals['sources.json'])
    manifest['observed_revisions']['augment_icons_deployed_20261112'] = 'main PR420/1568fb710b6441fe70bca5f9fc40f6dd805c20dc; source00ee567f; reviewed release hashes and verified activation/publication'
    manifest['topics']['augment-icons'] = [
        {'root': ROOT.as_posix(), 'path': name, 'role': role,
         'sha256': hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}
        for name, role in (
            ('server-mods/code/common/item_instance.cpp', 'Deployed ornament mask and actual native selection/update methods'),
            ('server-mods/code/zone/client_packet.cpp', 'Deployed ornament-operation gates preserve explicit transformations'),
            ('server-mods/code/common/item_instance.h', 'Actual ornament socket enum and instance cosmetic accessors'),
            ('tools/tests/test_augment_ornament_native.py', 'Actual production-method native regression runner'),
            ('tools/tests/fixtures/augment_ornament.cpp', 'Stat/ornament/socket/missing-data/stale-field controls'),
            ('docs/items/augment-icons-20261112/README.md', 'Cause, source/test boundary, safe recovery limits, exact player QA and whole-wiki impact'),
            ('docs/items/augment-icons-20261112/verification.json', 'Dated focused verification; player acceptance separate'),
            ('docs/items/augment-icons-20261112/native-build.json', 'Three reproduced baselines, candidate identities and authenticated dependencies'),
            ('docs/items/augment-icons-20261112/repair.py', 'Single-column full-row guarded repair'),
            ('docs/items/augment-icons-20261112/rollout.py', 'Reviewed one-shot production operator and preserved-state gates'),
            ('docs/items/augment-icons-20261112/repair-rehearsal.json', 'Actual MariaDB atomicity/drift/forward/replay proof'),
            ('docs/items/augment-icons-20261112/production-verification.json', 'Fresh running identities and five-row preservation receipt'),
            ('docs/items/augment-icons-20261112/wiki-public-verification.json', 'All613public hashes, headers and private denials'))]
    updated['sources.json'] = json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'
    patch = ''.join(''.join(difflib.unified_diff(originals[name].splitlines(True), value.splitlines(True),
                                               fromfile='a/references/' + name, tofile='b/references/' + name))
                    for name, value in updated.items())
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'installed-skill.patch').write_text(patch, encoding='utf-8')
    if apply:
        for name, original in originals.items():
            if (SKILL / 'references' / name).read_text(encoding='utf-8') != original:
                raise RuntimeError('Installed knowledge changed during preparation: ' + name)
        for name, value in updated.items():
            (SKILL / 'references' / name).write_text(value, encoding='utf-8')
    print(json.dumps({'applied': apply, 'patch': str(OUT / 'installed-skill.patch'), 'files': list(updated)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    main(parser.parse_args().apply)
