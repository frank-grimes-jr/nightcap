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
HEADING = '## Stat augment icons — November 12 local correction, not deployed'
SECTION = '''## Stat augment icons — November 12 local correction, not deployed

Source E:/EQ_Local_Dev/_worktrees/augment-item-icons, codex/augment-item-icons;
docs/items/augment-icons-20261112/README.md owns cause, tests and exact owner QA.
ItemInstance::IsOrnamentationAugment previously accepted empty/ordinary IDFile
as cosmetic intent and compared AugType masks to literal socket numbers20/21.
UpdateOrnamentationInfo then copied ordinary Hunt augment icons to host items.
Candidate checks actual type20/21bits and retains explicit Hero's Forge fallback.
Stat augments cannot win by IDFile; real ornaments behind them remain supported.
Actual three production bodies/enum compile and run in
tools/tests/test_augment_ornament_native.py + fixtures/augment_ornament.cpp.
Old type22/empty-IDFile case fails before fix and passes after. Related augment,
trade and metadata controls pass; no full runtime build or owner rendering claim.

No definitions/rules/schema/ItemData/cache-format/client change. Rebuild affected
native consumers from current released retained source; preserve metadata-aware
world/zone/shared_memory and newer releases. OVH needs supported whole-runtime
activation; quest/rule reload cannot load C++. No new client download/cache rebuild
is needed by this predicate change. Existing saved ornament_icon/ornament_idfile
reload unchanged, so relogging alone is not a repair. Capture identified affected
rows freshly, prove accidental cosmetic origin, guard full preimages and repair
only confirmed cosmetic fields. Preserve earned augments/charges/dye/binding/
custom data/GUID. Never bulk-clear ornaments or restore player snapshots.
Source-only candidate: deployment, existing-row repair and owner visual QA OPEN.
All42authored wiki articles plus generated/catalog/home/Features/commands reviewed;
five owning/status/history previews say Not released. Historical global wiki
drift stays REVIEW REQUIRED; no ledger advance or publication is claimed.
'''


def main(apply):
    originals = {name: (SKILL / 'references' / name).read_text(encoding='utf-8')
                 for name in ('items.md', 'sources.json')}
    items = originals['items.md']
    if HEADING in items:
        start = items.index(HEADING)
        next_heading = items.find('\n## ', start + len(HEADING))
        items = items[:start] + items[next_heading + 1:] if next_heading >= 0 else items[:start]
    title_end = items.index('\n') + 1
    updated = {'items.md': items[:title_end] + '\n' + SECTION + '\n' + items[title_end:].lstrip('\n')}
    manifest = json.loads(originals['sources.json'])
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    manifest['observed_revisions']['augment_icons_candidate_20261112'] = revision + ' + reviewed candidate file hashes'
    manifest['topics']['augment-icons'] = [
        {'root': ROOT.as_posix(), 'path': name, 'role': role,
         'sha256': hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}
        for name, role in (
            ('server-mods/code/common/item_instance.cpp', 'Reviewed ornament-mask predicate and actual selection/update bodies; local candidate only'),
            ('server-mods/code/common/item_instance.h', 'Actual ornament socket enum and instance cosmetic accessors'),
            ('tools/tests/test_augment_ornament_native.py', 'Actual production-method native regression runner'),
            ('tools/tests/fixtures/augment_ornament.cpp', 'Stat/ornament/socket/missing-data/stale-field controls'),
            ('docs/items/augment-icons-20261112/README.md', 'Cause, source/test boundary, safe recovery limits, exact player QA and whole-wiki impact'),
            ('docs/items/augment-icons-20261112/verification.json', 'Dated focused and wiki verification; not deployment or player acceptance'))]
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
