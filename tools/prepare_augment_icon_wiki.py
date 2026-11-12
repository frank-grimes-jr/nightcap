"""Reproduce the published wiki before making only the icon-repair guide delta."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'docs/items/augment-icons-20261112'
ART = ROOT / 'artifacts/augment-icons-20261112'
OLD = Path('E:/EQ_Local_Dev/_worktrees/adventure-journal-endgame/artifacts/last-lantern-20261107')
RELEASE = '20261112-augment-icons-v1'
NOTES = {
    'equipment': '<h2 id="augment-icon-candidate">Stat augments and equipment icons</h2><p>Ordinary stat augments keep the equipment\'s own icon and appearance. Genuine cosmetic ornaments still change appearance. If an older item displays an augment icon, report the item name and slot to the owner; do not destroy augments as a workaround.</p>',
    'zone-hunt': '<h2 id="augment-icon-candidate">Socketed armor icons</h2><p>Hunt stat augments keep their own gem icons without changing the host armor icon or model. Bonuses and socket rules remain the same. <a href="equipment.html#augment-icon-candidate">Older affected equipment</a>.</p>',
    'augment-audit': '<h2 id="augment-icon-candidate">Socketed equipment icons</h2><p>The gem artwork describes the augment itself. Socketing an ordinary stat augment keeps the host equipment\'s own icon and appearance. <a href="equipment.html#augment-icon-candidate">Report older affected equipment</a>.</p>',
    'unreleased': '<h2 id="augment-icon-candidate">Augment icon correction — live testing</h2><p>The native correction is deployed: stat augments preserve equipment icons and genuine cosmetic transformations. Full player visual acceptance remains open. <a href="equipment.html#augment-icon-candidate">Equipment guidance</a>.</p>',
    'recent-changes': '<h2 id="augment-icon-candidate">November 12: augment icon correction — live testing</h2><p>Ordinary stat augments now preserve equipment icons and existing cosmetic transformations. Genuine ornaments remain supported. Older affected items are repaired individually while preserving augments and other item data. No client update is required; player visual acceptance remains open. <a href="equipment.html#augment-icon-candidate">Equipment guidance</a>.</p>',
}


def files(folder):
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in folder.rglob('*') if p.is_file()}


if __name__ == '__main__':
    destination = ART / 'wiki-source'
    assert not (HERE / 'wiki-candidate.json').exists()
    if not destination.exists():
        shutil.copytree(OLD / 'wiki-source', destination)
    elif not (destination / 'config').exists():
        # Resume the construction-only attempt that lacked its config sibling.
        shutil.copytree(OLD / 'wiki-source/config', destination / 'config')
    wiki = destination / 'wiki'
    sys.path.insert(0, str(wiki))
    import build
    out = build.build()
    baseline = json.loads((OLD / '20261107-last-lantern-v2.tar.json').read_text(encoding='utf-8'))
    assert files(out) == baseline, 'Current public source does not reproduce; do not publish a mirror'
    for name, note in NOTES.items():
        for directory in (wiki, ROOT / 'wiki'):
            path = directory / 'articles' / (name + '.json')
            data = json.loads(path.read_text(encoding='utf-8'))
            start = data['body'].find('<h2 id="augment-icon-candidate">')
            if start >= 0:
                data['body'] = data['body'][:start].rstrip()
            data['body'] += '\n' + note
            data['updated'] = data['reviewed_at'] = '2026-11-12'
            source = 'docs/items/augment-icons-20261112/README.md; authorized native deployment; player visual QA open'
            data['sources'] = [s for s in data['sources'] if 'augment-icons-20261112/' not in s] + [source]
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    result = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-m', 'unittest',
                             'test_wiki.WikiTests.test_every_local_link_asset_and_anchor',
                             'test_wiki.WikiTests.test_search_index_has_all_articles_without_internal_sources',
                             'test_wiki.WikiTests.test_public_payload_excludes_private_material'],
                            cwd=wiki, text=True, capture_output=True, timeout=180)
    assert result.returncode == 0, result.stderr[-1500:]
    current = files(out)
    changed = sorted(n for n in current if current[n] != baseline[n])
    assert set(current) == set(baseline) and set(changed) == {n + '.html' for n in NOTES} | {'search-index.json'}
    build.package(out, ART / (RELEASE + '.tar.gz'))
    report = {'result': 'candidate_not_published', 'baseline_release': '20261107-last-lantern-v2',
              'release': RELEASE, 'files': len(current), 'changed_existing': changed,
              'preserved_files': len(current) - len(changed), 'public_source_reproduced': True,
              'final_site_checks_passed': 3, 'scope': 'Five owning/status/history guides and search only; no player data or catalog changes'}
    (HERE / 'wiki-candidate.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))
