"""Refresh reviewed AA knowledge after verified activation; preserve other topics."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SKILL = Path('C:/Users/verre/.codex/skills/nightcap-development')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replace_section(text, heading, next_heading, replacement):
    start = text.index(heading)
    end = text.index(next_heading, start)
    return text[:start] + replacement.rstrip() + '\n\n' + text[end:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    activation = json.loads((HERE / 'server-receipt.json').read_text())
    health = json.loads((HERE / 'final-health.json').read_text())
    assert activation['gateway_open'] and health['status'] == 'healthy'
    assert health['runtime']['image_id'] == activation['runtime']['image_id']
    assert health['runtime']['restart_count'] == 0
    revision = json.loads((HERE / 'deployment/manifest.json').read_text())['source_commit']
    files = ['references/balance.md', 'references/multiclass.md', 'references/sources.json']
    before = {name: (SKILL / name).read_bytes() for name in files}
    decoded = {name: raw.decode('utf-8').replace('\r\n', '\n') for name, raw in before.items()}
    block = f'''## Buried Sea AA policy — deployed for owner QA October 13

Current implementation/evidence: `{ROOT.as_posix()}/docs/releases/aa-tbs-20261013/README.md`.
Feature/dev/test candidate `{revision[:7]}` is live on OVH with image
`{activation['runtime']['image_id']}`. Main promotion and owner in-game balance,
readability and enjoyment acceptance remain pending. The concurrent October 13
skill-progression/offhand correction and signed client2026101301 were retained.

`era.json` selects `config/aa-policy.json`; `tools/aa_tbs_policy.py` generates
`common/nightcap_aa_policy.h` from a reviewed full catalog fixture. Unknown rank
identities fail closed. TBS13 is an AA-only bound, independent of Classic world
expansion. Most families cap at3 ranks at30/40/50; core passives at1 or10/20/30.
Dependencies can raise levels/remove ranks, never widen the pool. Six exceptions:
Eyes Wide Open938 rank8 at1; Diminutive543 rank1 at10; ENC Pet Discipline3202
rank1 at20 with Animation Empathy195 rank3; Durability3512/Agility3818 ranks1/2/3
at30/40/50; Sturdy1403 rank1 at50 (raw AC, not percent mitigation).

High-risk TBS burns/executes/refills/glyphs and all grant-only veteran families
are dormant. Existing earned ranks, charges, wallets and spent accounting are
preserved, with no refunds or repurchase charges. Native CanUse gates offers,
grants, purchase, activation and usable projection. ReprojectEarnedAAs handles
same-zone levels before bonus/save; full AA refresh clears/resends table, owned
ranks and stats. Missing prerequisite definitions reject purchases.

Global ceiling390 families/941 ranks; sampled triples start at9 families at1,
about15–16 at10–20. Exact 16-class/six-union coverage and maximum legal spend are
in coverage.json; these are catalog counts, not encounter strength measurements.
5 policy tests,5,646 native rank/level cases plus actual purchase/save/projection
checks,13 deployment/preflight tests and9 preserved skill scenarios passed.
Independent review fixed missing prerequisites/incomplete refresh and checked
the final retained-source build. All12 running zones match;47 player/11 custom
tables, rules, AA content and existing services were preserved through restart.

Future policy edits require regeneration and a matching zone deployment;
era SQL/rule/AA reload cannot install a compiled allowlist. No new world rule or
client asset is needed. Production child exits restart the entire runtime; use
the release's guarded operator and image-only recovery, never old player SQL.
Pet avoidance/AC is live; pet HP updates on summon/restore, with saved HP clamped.
Temporary spell buffs expire normally. Existing cross-class Mastery of the Past
prerequisite behavior is outside this change. Resummon pets for HP cap QA.

The preceding audit remains at docs/audits/aa-tbs-20261013: all6,655 DB rank level
requirements are1 and there are no expansion13 rows. Compiled policy now supplies
independent level gates; do not interpret untouched DB rows as unrestricted live
access. No fresh encounter campaign or player acceptance was claimed.
'''
    decoded['references/balance.md'] = replace_section(decoded['references/balance.md'],
        '## Buried Sea AA audit', '## Source routes', block)
    summary = f'''## AA catalog policy — deployed for owner QA October 13

The TBS cutoff and six utility/pet exceptions are active in a compiled native
allowlist, with staged early caps. See [balance](balance.md) and
`{ROOT.as_posix()}/docs/releases/aa-tbs-20261013/README.md` for exact ranks,
source, tests, rollback and owner QA. Main promotion/player acceptance is pending.
World stays Classic; all DB AA definitions and purchases remain intact. Higher
earned ranks and veteran grants are dormant; no refund or duplicate purchase.

`aa.cpp::CanUseAlternateAdvancementRank` checks generated rank identity and level;
`ReprojectEarnedAAs` derives active ranks without losing canonical counts/charges.
`exp.cpp::SetLevel` reprojects before bonuses/save, and AA refresh sends clear,
table, points and stats. Missing prerequisite definitions fail purchase closed.
Pet HP changes on summon/restore; avoidance/AC uses current owner bonuses.
Only zone needs rebuilding for this policy; no new rule catalog or client asset.
The concurrent fully rebuilt skill/offhand fix and signed2026101301 remain paired.
All12 zone hashes and47 player/11 custom table preservation passed; no owner
balance/readability acceptance or fresh combat measurements are implied.
'''
    decoded['references/multiclass.md'] = replace_section(decoded['references/multiclass.md'],
        '## AA catalog policy audit', '## Skills and AA ownership', summary)
    manifest = json.loads(decoded['references/sources.json'])
    manifest['basis'] = manifest['basis'].replace(
        'AA TBS catalog audit refreshed October 13 from read-only production content and reviewed integrated AA/attack source; no new combat or deployment acceptance.',
        'AA TBS policy refreshed October 13 from reviewed native implementation, tests and verified OVH candidate deployment; owner gameplay acceptance remains pending.')
    manifest['observed_revisions']['aa_tbs_policy_20261013'] = revision
    common = {
        'config/aa-policy.json': 'authoritative Classic TBS caps and named exceptions',
        'server-mods/code/common/nightcap_aa_policy.h': 'generated native fail-closed rank/level allowlist',
        'tools/aa_tbs_policy.py': 'reviewed deterministic dependency closure and generation',
        'tools/tests/test_aa_tbs_policy.py': 'policy exception, prefix, dependency and generation checks',
        'tools/tests/verify_aa_tbs_native.py': 'actual native eligibility, purchase, save and projection checks',
        'docs/releases/aa-tbs-20261013/README.md': 'verified deployment, preserved baseline, limits and exact owner QA',
        'docs/releases/aa-tbs-20261013/server-receipt.json': 'closed-state player/custom preservation and twelve native hashes',
        'docs/releases/aa-tbs-20261013/final-health.json': 'dated post-deployment runtime health; not gameplay acceptance'
    }
    for topic in ('balance', 'multiclass'):
        entries = manifest['topics'][topic]
        for entry in entries:
            if entry['path'] in ('server-mods/code/zone/aa.cpp', 'server-mods/code/zone/exp.cpp', 'server-mods/code/zone/client.h') or 'docs/audits/aa-tbs-20261013/' in entry['path']:
                entry.update(root=ROOT.as_posix(), revision=revision,
                             sha256=sha((ROOT / entry['path']).read_bytes()))
                if entry['path'].endswith('aa.cpp'):
                    entry['role'] = 'reviewed TBS policy, earned/usable projection and complete AA refresh'
                elif entry['path'].endswith('exp.cpp'):
                    entry['role'] = 'XP allocation and level-triggered AA projection before bonuses/save'
        for path, role in common.items():
            new = dict(root=ROOT.as_posix(), path=path, role=role, revision=revision,
                       sha256=sha((ROOT / path).read_bytes()))
            index = next((i for i, e in enumerate(entries) if e['path'] == path), None)
            if index is None:
                entries.append(new)
            else:
                entries[index] = new
    decoded['references/sources.json'] = json.dumps(manifest, indent=2) + '\n'
    stage = HERE / 'skill-update'
    stage.mkdir(exist_ok=True)
    patch = []
    for name in files:
        output = stage / name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(decoded[name], encoding='utf-8', newline='\n')
        patch.extend(difflib.unified_diff(before[name].decode('utf-8').splitlines(True),
                     decoded[name].splitlines(True), fromfile=str(SKILL / name), tofile=str(SKILL / name)))
    (HERE / 'nightcap-skill-update.patch').write_text(''.join(patch), encoding='utf-8', newline='\n')
    if args.install:
        assert all((SKILL / name).read_bytes() == raw for name, raw in before.items()), 'Skill changed during preparation'
        for name in files:
            target = SKILL / name
            temp = target.with_name(target.name + '.aa-tbs.tmp')
            with temp.open('xb') as f:
                f.write((stage / name).read_bytes())
            os.replace(temp, target)
    receipt = {'installed': args.install, 'implementation_revision': revision,
               'files': {name: {'before': sha(before[name]), 'after': sha((stage / name).read_bytes())} for name in files}}
    (stage / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
