"""Reproduce current public wiki before preparing the scoped DoT guide delta."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'docs/balance/dot-initial-damage-20261112'
ART = ROOT / 'artifacts/dot-no-initial-damage-20261112'
OLD = Path('E:/EQ_Local_Dev/_worktrees/imitate-death-no-cooldown/artifacts/imitate-death-20261112')
RELEASE = '20261112-dot-ticks-v2'
PREVIOUS = '20261112-imitate-death-v1'
NOTES = {
    'combat': '<h2 id="dot-initial-damage">Damage-over-time spells: ticks without an initial hit</h2><p>Player DoTs keep instant casting, but no longer deal their separate cast-time damage hit. Disease Cloud and Poison Bolt are examples that previously had this extra hit. Damage begins on the normal tick timer; casting just as a tick occurs can still show tick damage immediately. Recasting does not create an extra direct hit. DoTs without a separate initial hit, such as Clinging Darkness and Heat Blood, keep their current behavior. Tick damage, debuffs, mana costs and reuse limits remain. Positive one-time heals, ordinary nukes and NPC casting retain their existing behavior. No client download is needed. Gameplay and combined-build balance acceptance remain under live testing.</p>',
    'unreleased': '<h2 id="dot-initial-damage">DoT landing damage removed — live testing</h2><p>Player DoTs keep instant casts and normal ticks while losing the separate immediate damage hit on spells that have one. No client download is needed. <a href="combat.html#dot-initial-damage">Examples and test expectations</a>. Owner gameplay and balance acceptance remain open.</p>',
    'recent-changes': '<h2 id="dot-initial-damage-20261112">November 12: DoT initial damage removed — live testing</h2><p>Player DoTs no longer deal their separate cast-time damage hit. Instant casting and normal ticks remain, and DoTs that had no initial hit keep their current behavior. Positive one-time heals, ordinary nukes and NPC casting are unchanged. No client download is needed. <a href="combat.html#dot-initial-damage">Examples and timing details</a>. Gameplay and balance acceptance remain open.</p>',
}


def files(folder):
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in folder.rglob('*') if p.is_file()}


if __name__ == '__main__':
    destination = ART / 'wiki-source-v2'
    assert not destination.exists(), 'Inspect existing preparation; do not overwrite it'
    shutil.copytree(OLD / 'wiki-source', destination)
    wiki = destination / 'wiki'
    sys.path.insert(0, str(wiki))
    import build
    out = build.build()
    baseline = json.loads((OLD / (PREVIOUS + '.tar.json')).read_text(encoding='utf-8'))
    assert files(out) == baseline, 'Current public source not reproduced'
    for name, note in NOTES.items():
        path = wiki / 'articles' / (name + '.json')
        data = json.loads(path.read_text(encoding='utf-8'))
        body = data['body']
        assert 'id="dot-initial-damage' not in body
        data['body'] = note + '\n' + body if name == 'recent-changes' else body.rstrip() + '\n' + note
        data['updated'] = data['reviewed_at'] = '2026-11-12'
        data['sources'].append('docs/balance/dot-initial-damage-20261112/DEPLOYMENT.md; owner-authorized live testing; acceptance open')
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    result = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-m', 'unittest',
        'test_wiki.WikiTests.test_every_local_link_asset_and_anchor',
        'test_wiki.WikiTests.test_search_index_has_all_articles_without_internal_sources',
        'test_wiki.WikiTests.test_public_payload_excludes_private_material'],
        cwd=wiki, text=True, capture_output=True, timeout=180)
    (HERE / 'wiki-release-tests.log').write_text(result.stdout + '\n' + result.stderr, encoding='utf-8')
    assert result.returncode == 0, result.stderr[-2000:]
    out = build.build()
    current = files(out)
    changed = sorted(n for n in current if current[n] != baseline[n])
    assert set(current) == set(baseline)
    assert set(changed) == {n + '.html' for n in NOTES} | {'search-index.json'}
    build.package(out, ART / (RELEASE + '.tar.gz'))
    report = {'result': 'prepared_not_published', 'baseline_release': PREVIOUS,
              'release': RELEASE, 'files': len(current), 'changed_existing': changed,
              'preserved_files': len(current) - len(changed),
              'baseline_source_reproduced': True, 'public_source_reproduced': False,
              'requires_baseline_publication': PREVIOUS,
              'public_checks_passed': 3, 'whole_wiki_review': 'All42authored sources, Home, Features, commands, catalogs and generated item/zone impacts assessed; only three owning/status/history guides and search change'}
    (HERE / 'wiki-candidate.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
