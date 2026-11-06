"""Prepare exact installed-knowledge patch; apply only with --apply (outside workspace)."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
from augment_audit import ROOT, OUT

SKILL = Path('C:/Users/verre/.codex/skills/nightcap-development')


def section(text, old_heading, replacement):
    start = text.index(old_heading)
    end = text.index('\n## ', start + len(old_heading))
    return text[:start] + replacement.rstrip() + '\n' + text[end:]


def main(apply):
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    originals = {n: (SKILL / 'references' / n).read_text(encoding='utf-8') for n in ('items.md', 'wiki.md', 'operations.md', 'sources.json')}
    changed = {}
    changed['items.md'] = section(originals['items.md'], '## Regular combat augments — October29 on test, not deployed', f'''## Zone augment audit — November6 candidate, not deployed

Source: {ROOT.as_posix()}, feature/augment-audit-20261106,
reviewed {revision}. Supersedes the narrower October29 unpublished
regular-static-combat candidate. Fresh read-only production capture:48Classic
pools at1.5%, eight disabled, two managed expeditions at0.5%;58families/232augments.
Zero of585guard spawn/NPC pairs are in the old6056-entry equipment allowlist.

Candidate augments roll for any unowned killable NPC, including guards, named,
quest/merchant NPCs and scripted adds; no source/name/level/class/night gates.
Owned pets captured before charm fade, mercs/swarm, protected/noncombat actors
and restored corpses remain excluded. Corpse ownership remains. Killable merchants
can leave corpses in enabled reward zones; no city pool/policy change. Equipment
keeps old gates. Award follows dungeon loot cleanup, preserving High Keep guard
augments. Managed186 uses Blackspire940592–595 and independently inherits76gear,
source/minimum/night/chance. Only186and Classic CT48enable; six access-check pools
stay off. Expedition rolls become1.5%; static per-life receipts and35%static
miniboss relic gates remain; dynamic enemies get one RNG augment roll/life.

Specialties: avoidance, real shield block, damage/healing, spell haste, mana
preservation, Faerune, dodge, Shielding, Accuracy and Spell Shielding. Config:
config/augment-specialties.json; generator tools/augment_audit.py. Primary/heroic/
level budgets and60/30/8/2quality plus3/4/4forge remain. Six copies max24Avoidance,
30Accuracy,6Shielding,12SpellShielding,48raw damage/heal. Existing caps include750
damage/heal plus30earned headroom; no new cap/rule. Strongest Hunt shield block
max2percentage points, usable shield required; lore describes it. Existing stock
focus/dodge/Faerune IDs and correct types are captured; strongest worn/focus rules
apply, additive-worn rule0 is guarded. All232icons become visually reviewed stock
gems/orbs/crystals944–967. RoF2 grid is VERTICAL, index icon-500: row-major mapping
would accidentally select equipment. Protected client is read-only.

Sources: zone_hunt.cpp/.h, zone_hunt_policy.h, bonuses.cpp, attack.cpp,
dungeon_service.cpp. Tests: test_zone_hunt_native.py, test_augment_audit.py,
test_augment_expedition_native.py; actual bodies, full10000-value RNG domains,
six-socket/eligibility controls.52focused tests pass. Disposable MariaDB proves232
full afterimages, exact inverse and replay/drift/stacking/state rejection. Four
complete TUs compile;144retained native link inputs first reproduce Nov4live
baseline335cbce1 byte-for-byte, then link candidatebc88a468. Existing live Hate
spawn mapping is preserved rather than overwritten by main's selective mirror.

Evidence/full58-item list/icons/QA/runbook: docs/audits/augments-20261106/.
This is a linked local candidate, no production content writes, MAIN/OVH promotion,
public wiki publication or player acceptance. Current world/zone/shared_memory
metadata consumers, quests and stock client must remain compatible. Activation
needs a fresh stopped backup, guarded SQL, matching regenerated shared item cache
and supported whole-runtime restart; rule/quest reload is insufficient. No new
client asset. Inverse retains earned inventories/receipts; never restore players
or use pre-Power-Source-XP binaries. Exact guard/add/expedition/stacking/icon/solo
balance QA remains mandatory. Historical missing Ashen client-archive fixture is
unavailable; no client acceptance is inferred.
''')
    changed['wiki.md'] = section(originals['wiki.md'], '## Regular combat augments — October29 unpublished candidate', f'''## Zone augment audit — November6 unpublished preview

Source: {ROOT.as_posix()}, {revision}.
All41authored articles and generated item/zone impacts are assessed in
docs/audits/augments-20261106/wiki-review.json. An explicitly Not released58-family
augment-audit article, owning guides, Features, In development and Change Log
describe broad NPC drops, moderate secondary specialties and exotic icons.
Existing published item values/48-zone catalog/release labels remain; generated
augment/zone pages link the preview. Home goal paths and commands need no change.
22wiki/content-refresh/preview tests pass; local build/link checks do not establish
public publication. Historical global source drift stays REVIEW REQUIRED; no
blanket ledger advancement. Six dormant pools remain excluded; CT/Hate B enable
only in the candidate. Publication/catalog promotion requires verified authorized
activation and separate owner gameplay acceptance. Protected-client icon extracts
are audit evidence, not a client asset release. Preserve newer public source when
preparing any eventual publication.
''')
    changed['operations.md'] = section(originals['operations.md'], '## Current native baseline — November1 placeholder-loot zone', '''## Current native baseline — November4 Power Source training display

Dated release evidence in current main records OVH activation November4 09:55UTC:
docs/releases/power-source-xp-display-20261103/README.md, zone335cbce1d046565da3ad013261080de4df5032703719a2b2d8348f73f1830dd1,
image da797daf over3999a935. Retained local source/build:
/tmp/nightcap-power-source-xp-display-20261103-v1 in akk-stack-eqemu-server-1.
It includes Power Source metadata, SSF, per-zone Hunt rates and placeholder-loot
repair. Never start a new native build from the older November1/Hate baseline or
roll back to pre-XP metadata consumers after training. This is release-document
evidence, not a fresh production native probe; owner display/gameplay QA is open.

The November6 augment candidate independently reproduces both retained unstripped
and shipping zone bytes from144authenticated link inputs before linking its delta.
Main's selective dungeon_service.cpp mirror lacks the already-live Hate spawn
source join correction; inspect/preserve that hunk. Native compilation needs the
retained CMake flags and PCH header. Packaging uses strip --strip-debug and the
ELF runtime-identity verifier, not default strip-all. No candidate install/restart
or standing production approval is implied. Evidence:
docs/audits/augments-20261106/{native-compile.json,native-link.json,README.md}.
''')
    manifest = json.loads(originals['sources.json'])
    manifest['observed_revisions']['augment_audit_20261106_candidate'] = revision + ' (local linked candidate; not deployed)'
    paths = ['server-mods/code/zone/zone_hunt.cpp', 'server-mods/code/zone/zone_hunt.h',
        'server-mods/code/common/zone_hunt_policy.h', 'server-mods/code/zone/bonuses.cpp',
        'server-mods/code/zone/attack.cpp', 'server-mods/code/zone/dungeon_service.cpp',
        'config/augment-specialties.json', 'tools/augment_audit.py',
        'tools/tests/test_zone_hunt_native.py', 'tools/tests/zone_hunt_death_fixture.cpp',
        'tools/tests/zone_hunt_load_fixture.cpp', 'tools/tests/test_augment_audit.py',
        'tools/tests/test_augment_expedition_native.py', 'wiki/augment_candidate.py',
        'wiki/articles/augment-audit.json', 'docs/audits/augments-20261106/verification.json',
        'docs/audits/augments-20261106/native-link.json', 'docs/audits/augments-20261106/mariadb-rehearsal.json']
    entries = [dict(root=ROOT.as_posix(), path=p, role='November6 reviewed augment candidate; tested/linked locally, no deployment or player acceptance',
                    revision=revision, sha256=hashlib.sha256((ROOT / p).read_bytes()).hexdigest()) for p in paths]
    manifest['topics']['augment-audit'] = entries
    bypath = {e['path']: e for e in entries}
    for entry in manifest['topics']['items']:
        if entry['path'] in bypath:
            entry.update(bypath[entry['path']])
    changed['sources.json'] = json.dumps(manifest, indent=2) + '\n'
    directory = OUT / 'skill-update'
    directory.mkdir(exist_ok=True)
    patch = ''.join(''.join(difflib.unified_diff(originals[n].splitlines(True), changed[n].splitlines(True),
                fromfile='a/references/' + n, tofile='b/references/' + n)) for n in changed)
    (directory / 'installed-nightcap.patch').write_text(patch, encoding='utf-8')
    if apply:
        for name, text in changed.items():
            (SKILL / 'references' / name).write_text(text, encoding='utf-8', newline='\n')
    print(json.dumps({'status': 'applied' if apply else 'prepared; installation pending', 'revision': revision,
                      'files': list(changed), 'reviewed_source_entries': len(entries), 'patch': str(directory / 'installed-nightcap.patch')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    main(parser.parse_args().apply)
