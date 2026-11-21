"""Prepare review records, candidate wiki notes and an exact installed-skill patch."""
from pathlib import Path
import difflib
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SKILL = Path('C:/Users/verre/.codex/skills/nightcap-development')
REF = 'docs/releases/aa-purchase-latency-20261121/README.md'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main():
    note = ('<h2 id="aa-purchase-latency">AA purchase smoothness — not released</h2>'
            '<p>A server fix is ready for testing to reduce the brief game freeze '
            'when purchasing an AA. AA costs, earned ranks and cooldowns are unchanged. '
            'The fix is not installed yet; in-game confirmation remains open.</p>')
    for name in ('unreleased', 'recent-changes'):
        path = ROOT / 'wiki/articles' / (name + '.json')
        article = json.loads(path.read_text(encoding='utf-8'))
        if 'id="aa-purchase-latency"' not in article['body']:
            article['body'] = note + '\n' + article['body']
            article['sources'].append(REF + '; local candidate, not deployed or player accepted')
            article['updated'] = '2026-11-21'
            save(path, article)
    save(HERE / 'wiki-impact.json', {
        'source': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'includes_worktree': True, 'publication': 'PENDING; candidate source only',
        'changed': ['unreleased', 'recent-changes'],
        'review': {
            'multiclass/combat/launcher': 'No purchase steps, costs, ownership, cooldown or client-update instructions change.',
            'home/features/commands': 'Performance repair; no new feature, command or major departure from Classic.',
            'generated_items/zones/catalogs/build_lab': 'No item, zone, rank, effect, numeric or balance changes.',
            'other_guides': 'No acquisition, quest, trade, equipment, pet, travel or progression changes.',
            'ledger': 'Historical global source drift retained; do not advance unrelated reviewed revisions.',
        },
        'authored_pages': {p.stem: {'title': json.loads(p.read_text(encoding='utf-8'))['title'], 'sha256': sha(p)}
                           for p in sorted((ROOT / 'wiki/articles').glob('*.json'))},
    })
    save(HERE / 'validation.json', {
        'cooldown_tests': 21, 'native_rof2_checks': 49, 'adjacent_tests': 5,
        'baseline_regression': 'FAIL as expected: idle purchase sends100 resets',
        'candidate_regression': 'PASS', 'native_build': 'PASS; see build.json',
        'independent_review': 'No blocking findings; added requested rank-upgrade and passive-haste controls',
        'native_boundaries': 'SQL persistence, rendered window and live frame time not simulated',
        'deployment': 'NOT DEPLOYED', 'player_acceptance': 'OPEN',
    })
    reference = SKILL / 'references/multiclass.md'
    before = reference.read_text(encoding='utf-8')
    section = '''## AA purchase freeze — November21 candidate, not deployed

Every committed purchase previously sent a100-slot reset sweep. Pinned RoF2
receiver RVA0x0b5bd0 calls AA-window rebuild0x209f90 per packet; native49checks
confirm100updates. Purchase now passes its family to SendAlternateAdvancementTimers:
idle passive0timer packets; idle activated1reset; running timers reproject with
unchanged stored deadlines/current rank and haste. Reset an expired purchased
family and retire/reset stale Imitate Death; Quick Buff stays ready. The existing
no-argument login/class-change/bulk-reset route retains the full sweep.

Ownership transactions, prices, ranks, effects and authoritative durations remain.
Source E:/EQ_Local_Dev/_worktrees/aa-purchase-latency, zone/{aa.cpp,client.h}.
Tests tools/tests/test_aa_cooldown_identity.py (21tests, real rank/haste controls)
and eq-client-dll/tests/aa-reuse-native.cpp;5adjacent tests pass. Native shipping
predecessor13ad2534 reproduced exactly; fresh PCH/fullAA compilation and link pass.
Only a nonvirtual overload is added; Client layout/vtable/old symbol stay intact.
Rebuild zone; no SQL/rule/cache/client-download change. Supported whole-runtime
activation is required; never kill one production zone or restore player data.
Evidence/build pins/exact Arena/Chronicler QA: docs/releases/aa-purchase-latency-20261121/.
Candidate wiki notes are unpublished; historical global ledger drift stays open.
Production install, visible freeze retest and owner acceptance remain OPEN.

'''
    assert '## AA purchase freeze — November21' not in before
    after = before.replace('## AA availability', section + '## AA availability', 1)
    sources = SKILL / 'references/sources.json'
    old_sources = sources.read_text(encoding='utf-8')
    data = json.loads(old_sources)
    paths = ('server-mods/code/zone/aa.cpp', 'server-mods/code/zone/client.h',
             'tools/tests/test_aa_cooldown_identity.py', 'eq-client-dll/tests/aa-reuse-native.cpp',
             REF, 'docs/releases/aa-purchase-latency-20261121/build.json',
             'docs/releases/aa-purchase-latency-20261121/validation.json')
    entries = data['topics']['multiclass']
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    for path in paths:
        entries[:] = [e for e in entries if e['path'] != path]
        entries.append({'root': ROOT.as_posix(), 'path': path,
                        'role': 'Reviewed AA purchase-latency candidate; built/tested, NOT deployed or player accepted',
                        'revision': revision + ' + reviewed feature/aa-purchase-latency worktree',
                        'sha256': sha(ROOT / path)})
    data['observed_revisions']['aa_purchase_latency_candidate_20261121'] = revision + ' + reviewed worktree; not deployed'
    new_sources = json.dumps(data, indent=2, ensure_ascii=False) + '\n'
    patch = ''
    pins = {}
    for path, old, new in ((reference, before, after), (sources, old_sources, new_sources)):
        output = HERE / ('installed-' + path.name)
        output.write_text(new, encoding='utf-8')
        pins[str(path)] = {'before': sha(path), 'after': sha(output), 'prepared': output.name}
        patch += ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                             fromfile=str(path), tofile=str(path)))
    (HERE / 'installed-skill.patch').write_text(patch, encoding='utf-8')
    save(HERE / 'installed-skill-pins.json', pins)


if __name__ == '__main__':
    main()
