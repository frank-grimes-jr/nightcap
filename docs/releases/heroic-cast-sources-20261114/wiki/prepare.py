"""Stage the Heroic casting guides on the previously published wiki source."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = ROOT.parent / 'thj-bow-live/artifacts/thj-combat-wiki'
ART = ROOT / 'artifacts/heroic-cast-sources-wiki'
PREVIOUS = '20261113-archery-backstab-v2'
RELEASE = '20261114-heroic-cast-sources-v1'
CHANGED = ['combat.html', 'equipment.html', 'recent-changes.html', 'search-index.json']
REVIEW = 'docs/releases/heroic-cast-sources-20261114/wiki/README.md'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode())

def hashes(folder):
    return {f.relative_to(folder).as_posix():sha(f) for f in folder.rglob('*') if f.is_file()}

def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError('Missing or ambiguous source passage: ' + before)
    return text.replace(before, after)

def update_articles(site, reviewed):
    original = {
        'combat': 'Clients gain 0.1% per heroic INT on direct damage and per heroic WIS on direct healing before final caps.',
        'equipment': 'Each heroic INT point adds 0.1% direct damage. Each heroic WIS point adds 0.1% direct healing. DoTs and HoTs do not receive this multiplier.',
    }
    markers = {
        'combat': ('Each heroic INT point adds', ' DoTs and HoTs do not gain'),
        'equipment': ('On spell gem casts and activated AA spells', ' The separate Bard'),
    }
    for name in ('combat', 'equipment', 'recent-changes'):
        dest = site / 'articles' / (name + '.json')
        data = json.loads(dest.read_bytes())
        body = json.loads((reviewed / 'articles' / dest.name).read_bytes())['body']
        if name == 'recent-changes':
            marker = '<h2 id="heroic-casts">'
            assert body.count(marker) == 1 and marker not in data['body']
            start = body.index(marker)
            change = body[start:body.index('</p>', start) + len('</p>')]
            data['body'] = change + data['body']
        else:
            opening, closing = markers[name]
            assert body.count(opening) == 1
            start = body.index(opening)
            change = body[start:body.index(closing, start)]
            assert 'activated AA' in change and 'Procs' in change and 'combat skills' in change
            data['body'] = replace_once(data['body'], original[name], change)
        data['updated'] = data['reviewed_at'] = '2026-11-14'
        data['sources'].append(REVIEW)
        save(dest, data)

def main(reviewed):
    manifest = BASE / (PREVIOUS + '.tar.json')
    prior = ROOT / 'docs/releases/thj-combat-20261113/wiki'
    assert json.loads((prior / 'public-verification.json').read_bytes())['release'] == PREVIOUS
    origin = json.loads((prior / 'publication.json').read_bytes())
    assert origin['result'] == 'PASS' and origin['release'] == PREVIOUS
    assert sha(manifest) == json.loads((prior / 'candidate.json').read_bytes())['manifest_sha256']
    before = json.loads(manifest.read_bytes())
    ART.mkdir(parents=True, exist_ok=True)
    archive = ART / (RELEASE + '.tar.gz')
    cmd = [sys.executable, '-B', '-X', 'utf8']
    with TemporaryDirectory(prefix='source-', dir=ART) as tmp:
        candidate = Path(tmp) / 'source'
        shutil.copytree(BASE / 'wiki-source', candidate, ignore=shutil.ignore_patterns('dist','__pycache__'))
        wiki = candidate / 'wiki'
        subprocess.run(cmd + ['build.py'], cwd=wiki, check=True)
        assert hashes(wiki/'dist') == before
        update_articles(wiki, reviewed)
        subprocess.run(cmd + ['-m','unittest','test_wiki','test_refresh','test_public_language','test_loot_model','test_loot_refresh'], cwd=wiki, check=True)
        args = [] if archive.exists() else ['--package', str(archive)]
        subprocess.run(cmd + ['build.py', *args], cwd=wiki, check=True)
        after = hashes(wiki / 'dist')
        assert before.keys() == after.keys()
        assert sorted(p for p in before if before[p] != after[p]) == CHANGED
        assert json.loads(archive.with_suffix('.json').read_bytes()) == after
        for test in ('test_search.cjs','test_equipment.cjs','test_experience.cjs','test_build_lab.cjs','test_loot_finder.cjs'):
            subprocess.run(['node', test], cwd=wiki, check=True)
        index = json.loads((wiki / 'dist/search-index.json').read_bytes())
        assert any(row['slug'] == 'recent-changes' and 'Heroic spell damage and healing' in json.dumps(row) for row in index)
        for name in ('combat','equipment','recent-changes'):
            page = (wiki/'dist'/(name+'.html')).read_text(encoding='utf-8')
            assert 'activated AA' in page and ('Procs' in page or 'procs' in page)
        retained = ART / 'wiki-source'
        if not retained.exists():
            shutil.copytree(candidate, retained, ignore=shutil.ignore_patterns('dist','__pycache__'))
        for name in ('combat','equipment','recent-changes'):
            rel = Path('wiki/articles') / (name + '.json')
            assert sha(candidate / rel) == sha(retained / rel)
    report = dict(release=RELEASE, status='staged', published=False, predecessor=PREVIOUS,
                  predecessor_manifest_sha256=sha(manifest), predecessor_reproduced=True, files=len(after),
                  preserved_files=len(after)-len(CHANGED), changed=CHANGED, package_sha256=sha(archive),
                  manifest_sha256=sha(archive.with_suffix('.json')))
    save(HERE/'candidate.json', report)
    print(report)

if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--articles-from', type=Path, default=ROOT / 'wiki')
    main(cli.parse_args().articles_from)
