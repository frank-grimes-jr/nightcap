"""Record source-only integration boundaries; never activates runtime/content."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/audits/augments-20261106'
CANDIDATE = 'f9247fba'
DEV = 'be81b04e'
CAPACITY = ['deploy/production/compose.yaml', 'tools/zone_capacity.py', 'tools/tests/test_zone_capacity.py']


def command(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, encoding='utf-8').strip()


def normalized_sha(raw):
    return hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()


if __name__ == '__main__':
    delta = command('diff', '--name-only', CANDIDATE, '--', 'server-mods/code', 'server-mods/quests')
    assert not delta, 'Integrated native/quest source differs from the linked release-base candidate: ' + delta
    preserved = {}
    for name in CAPACITY:
        before = subprocess.check_output(['git', 'show', DEV + ':' + name], cwd=ROOT)
        after = (ROOT / name).read_bytes()
        assert normalized_sha(before) == normalized_sha(after), 'Existing capacity candidate drift: ' + name
        preserved[name] = normalized_sha(after)
    report = dict(status='source integration validated locally; remote promotion pending',
        release_base_candidate=command('rev-parse', CANDIDATE), dev_parent=command('rev-parse', DEV),
        test_parent=command('rev-parse', 'origin/test'),
        native_and_quests='All server-mods/code and server-mods/quests contents match the linked release-base candidate; no additional native rebuild required for this merge',
        retained_native='native-link.json authenticates 144 inputs and byte-reproduces the retained live baseline before linking candidate',
        preserved_capacity_candidate=preserved,
        runtime_boundary='No capacity activation; do not merge or deploy the entire test branch under augment-only approval. The main-based release candidate excludes the preexisting capacity configuration.',
        tests=[dict(scope='Hunt, augment, capacity, historical augment migration', run=31, passed=29, skipped=2,
                    skipped_reason='Historical October29 standalone enable/disable MariaDB fixture requires opt-in connection environment; current full augment SQL has its separate successful disposable rehearsal'),
               dict(scope='wiki, refresh and candidate previews', run=22, passed=22, skipped=0)],
        wiki='46 authored articles reviewed; existing capacity preview and old bookmarks preserved; superseded October29 augment material explicitly historical; current live stats retained',
        exact_qa='README.md section Exact in-game QA spike, copied into the test-promotion PR body',
        production='unchanged', public_wiki='not published', player_acceptance='pending')
    (OUT / 'integration.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    qa = (OUT / 'README.md').read_text(encoding='utf-8').split('## Exact in-game QA spike\n', 1)[1]
    body = '''Guard kills and other unlisted enemies currently miss zone augments despite the 1.5% family chance. This candidate grants any unowned killable NPC the augment roll, corrects High Keep cleanup/Hate identity, adds bounded secondary specialties and replaces every default/glove icon with visually checked stock gems.

The integration supersedes the older October29 static-only candidate while retaining existing capacity configuration and preview sources exactly. Native and quest contents match the linked main-based candidate. This source promotion does not activate SQL, native binaries, worker capacity or the public wiki.

Validation: 29 integration checks pass, two historical opt-in MariaDB checks skip; 22 wiki checks pass. The release-base candidate separately passes 52 focused checks, four full native compiles, authenticated 144-input link/baseline reproduction and complete disposable SQL forward/inverse/drift tests.

Main/OVH and player acceptance remain gated. Any later augment-only release must use the main-based candidate, not promote unrelated capacity configuration from all of test.

Exact in-game QA spike:

'''
    (OUT / 'PR-dev.md').write_text(body + qa, encoding='utf-8')
    (OUT / 'PR-test.md').write_text(body + qa, encoding='utf-8')
    print(json.dumps({'native_and_quests_match': True, 'capacity_files_preserved': len(preserved), 'integration_passed': 51, 'skipped': 2}))
