"""Reconcile completed deployment/publication evidence into maintained docs."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'docs/items/augment-icons-20261112'


def section(text, prefix, replacement):
    start = text.index(prefix)
    end = text.find('\n## ', start + len(prefix))
    return text[:start] + replacement.rstrip() + '\n' + (text[end:] if end >= 0 else '')


if __name__ == '__main__':
    live = json.loads((HERE / 'production-verification.json').read_text(encoding='utf-8'))
    wiki = json.loads((HERE / 'wiki-public-verification.json').read_text(encoding='utf-8'))
    assert live['status'] == wiki['status'] == 'PASS' and live['gateway_open']
    path = HERE / 'README.md'; text = path.read_text(encoding='utf-8')
    start = text.index('Status:'); end = text.index('2026. Worktree:', start)
    text = text[:start] + ('Status: deployed and repaired November 12, 2026; admissions open. Main PR420/\n'
        '1568fb71, built source00ee567f. Full native identity, five-row data preservation\n'
        'and public wiki verification pass. Owner visual/gameplay acceptance remains\n'
        'open. Original release base: origin/main b7e404b2, fetched November 12,\n') + text[end:]
    text = text.replace('Full native build, deployment, saved-row repair and owner visual/gameplay\nacceptance remain separate open gates.',
        'Native build, activation and the five identified saved-row repairs are complete.\nOwner visual/gameplay acceptance remains open. See production-verification.json.\nThe completed operator is one-shot; never replay activation or repair SQL.')
    text = section(text, '## Wiki impact review', '''## Wiki impact review

Reviewed all42authored articles, Home, Features, commands and generated item/zone
catalogs. Equipment, Zone hunt, augment audit, In development and Change Log now
describe the deployed fix and open visual QA. Home/Features need no minor-fix
announcement; commands, values, acquisition and generated catalogs do not change.
Exact prior613-file public source reproduced before six output changes;607files
retained. Wiki20261112-augment-icons-v1 is published: all613canonical HTTPS hashes,
security headers, five private denials and publisher rollback checks pass. All
five service identities and private downloads/config remain. No Nginx reload.
Historical global source drift remains REVIEW REQUIRED; no blanket ledger advance.
See wiki-candidate.json, wiki-publication.json and wiki-public-verification.json.
''')
    path.write_text(text, encoding='utf-8')
    changes = '''## 2026-11-12 — Augment icon fix and five-item repair deployed

Main PR420/1568fb71 corrects ornament detection to use actual type20/21 bits and
reject empty/ordinary model IDs as cosmetic intent. Native augmentation handlers
refresh cosmetics only for real ornament changes, preserving mold/quest overrides
during stat-only insert/remove/swap/destroy. Real ornaments remain supported.

Three live binary baselines reproduce exactly before isolated compilation/relink;
ELF identities,182actual dependencies/179authenticated source headers,17focused
checks and real MariaDB rollback/drift/forward/replay rehearsal pass. Supported
whole-runtime activation retains Last Lantern and all newer source/data systems.

Owner-authorized repair changes only ornament_icon in five confirmed equipped
Palwar rows. All205inventory rows retain their augments and every other field;
unrelated inventory is unchanged. Fresh stopped full backup, normal saved-state/
market checks, native/service identities and reopened admissions verify. No player
snapshot restore, client update, definition/stat/rule/cache-format change.

Wiki20261112-augment-icons-v1 verifies all613public hashes/headers/private denials,
retaining607files. Owner visual/gameplay QA remains open. Exact evidence, guarded
operator, recovery limits and QA: docs/items/augment-icons-20261112/.
'''
    path = ROOT / 'CHANGES.md'
    path.write_text(section(path.read_text(encoding='utf-8'), '## 2026-11-12', changes), encoding='utf-8')
    status = '''## November 12 — Augment icons repaired and fix deployed

Main PR420/1568fb71 and the matched native world/zone/shared_memory pair are
deployed; access is open. Stat augments preserve host icons and existing cosmetic
transformations. Five confirmed Palwar icon overrides were repaired with all
augments and every other field preserved across205inventory rows; unrelated
inventory is unchanged. Fresh stopped backup, native/boot/market checks and
independent running identity verification pass. No client update is required.
Wiki20261112-augment-icons-v1 verifies all613public hashes;607files retained.
Owner visual/gameplay acceptance stays open. [Evidence and exact QA](items/augment-icons-20261112/README.md).
'''
    path = ROOT / 'docs/status.md'
    path.write_text(section(path.read_text(encoding='utf-8'), '## November 12', status), encoding='utf-8')
    path = HERE / 'verification.json'; data = json.loads(path.read_text(encoding='utf-8'))
    data['scope'] = 'Compiled production methods/caller gates, authenticated native release, real SQL rehearsal and deployed repair/publication'
    data['release_focused_checks'] = {'passed': 17, 'includes': 'expanded transformation/cursor/real-ornament insert/remove/swap/destroy regression'}
    data['gates'] = {'native_build': 'PASS; three baseline reproductions and candidate identities', 'deployment': 'PASS; admissions open',
                     'saved_row_repair': 'PASS;5one-column changes,205rows otherwise preserved',
                     'public_wiki': 'PASS;613HTTPS hashes,607retained files', 'owner_in_game_QA': 'OPEN'}
    data['hashes'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in
                      (*data['hashes'], 'server-mods/code/zone/client_packet.cpp')}
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    path = HERE / 'wiki-review.json'; data = json.loads(path.read_text(encoding='utf-8'))
    data['publication'] = '20261112-augment-icons-v1;613canonical HTTPS hashes verified;607files retained'
    for row in data['authored_articles']:
        if row['decision'] == 'Not released candidate note added':
            row['decision'] = 'Deployed guide/status/history correction; owner visual QA remains open'
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    refresh = subprocess.run(['python', '-X', 'utf8', '-B', 'wiki/check_refresh.py', '--repo', '.', '--ref', 'HEAD', '--include-worktree'],
                             cwd=ROOT, text=True, capture_output=True, encoding='utf-8')
    assert refresh.returncode == 1 and json.loads(refresh.stdout)['result'] == 'REVIEW REQUIRED'
    (HERE / 'wiki-refresh.json').write_text(refresh.stdout, encoding='utf-8')
    print('Maintained docs reconciled with completed release; historical wiki drift retained.')
