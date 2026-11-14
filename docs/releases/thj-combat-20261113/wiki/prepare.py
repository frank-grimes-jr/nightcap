"""Package the combat-guide changes on the authenticated official site source."""
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
ART = ROOT / 'artifacts/thj-combat-wiki'
BASE = ROOT.parent / 'sympathetic-production/artifacts/sympathetic-prod/official-wiki-ste'
PREVIOUS = '20261113-sympathetic-clicks-v1'
RELEASE = '20261113-archery-backstab-v2'
FILES = ['combat.html', 'features.html', 'recent-changes.html', 'search-index.json']
SOURCES = ['docs/combat/thj-bows/QA.md', 'docs/combat/thj-backstab/QA.md']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())

def insert_guides(site, article_root):
    for name in ('combat', 'features', 'recent-changes'):
        relative = Path('articles') / (name + '.json')
        reviewed = json.loads((article_root / relative).read_bytes())
        path = site / relative
        article = json.loads(path.read_bytes())
        body = reviewed['body']
        sequence = ('backstab-weapons', 'bow-damage') if name == 'recent-changes' else ('bow-damage', 'backstab-weapons')
        for slug in sequence:
            if name == 'features':
                mark = '<p><a href="combat.html#' + slug + '">'
                assert body.count(mark) == 1
                start = body.index(mark) + len('<p>')
                end = body.index('</p>', start)
                block = '<li>' + body[start:end] + '</li>'
                key = '<li id="combat">'
            else:
                mark = '<h2 id="' + slug + '">'
                assert body.count(mark) == 1
                start = body.index(mark)
                end = body.find('<h2 id=', start + len(mark))
                block = body[start:end] if end >= 0 else body[start:]
                key = '<h2 id="melee-casting">' if name == 'combat' else '<h2 id="stock-sympathetic">'
            assert article['body'].count(key) == 1
            article['body'] = article['body'].replace(key, block + key)
        if name == 'combat':
            for word in ('archery', 'bow damage', 'Heroic Dexterity', 'Archery Mastery', 'Bow Mastery', 'Backstab', 'piercing'):
                if word not in article['keywords']:
                    article['keywords'].append(word)
        article['sources'].extend(s for s in SOURCES if s not in article['sources'])
        article['updated'] = article['reviewed_at'] = '2026-11-13'
        save(path, article)

def files(out):
    return {f.relative_to(out).as_posix(): sha(f) for f in out.rglob('*') if f.is_file()}

def main(article_root):
    ART.mkdir(parents=True, exist_ok=True)
    prior_receipt = ROOT / 'docs/releases/sympathetic-clicks-20261113/wiki/candidate.json'
    prev_manifest = BASE / (PREVIOUS + '.tar.json')
    assert sha(prev_manifest) == json.loads(prior_receipt.read_bytes())['manifest_sha256']
    base = json.loads(prev_manifest.read_bytes())
    python = [sys.executable, '-B', '-X', 'utf8']
    with TemporaryDirectory(dir=ART, prefix='build-') as tmp:
        checkout = Path(tmp) / 'source'
        shutil.copytree(BASE / 'wiki-source', checkout, ignore=shutil.ignore_patterns('dist', '__pycache__'))
        site = checkout / 'wiki'
        subprocess.run(python + ['build.py'], cwd=site, check=True)
        assert files(site / 'dist') == base
        insert_guides(site, article_root)
        subprocess.run(python + ['-m', 'unittest', 'test_wiki', 'test_refresh', 'test_public_language', 'test_loot_model', 'test_loot_refresh'], cwd=site, check=True)
        archive = ART / (RELEASE + '.tar.gz')
        args = [] if archive.exists() else ['--package', str(archive)]
        subprocess.run(python + ['build.py', *args], cwd=site, check=True)
        after = files(site / 'dist')
        assert after == json.loads(archive.with_suffix('.json').read_bytes())
        assert after.keys() == base.keys()
        changed = sorted(name for name in base if base[name] != after[name])
        assert changed == FILES, changed
        for test in ('test_search.cjs', 'test_equipment.cjs', 'test_loot_finder.cjs', 'test_experience.cjs'):
            subprocess.run(['node', test], cwd=site, check=True)
        index = json.loads((site / 'dist/search-index.json').read_bytes())
        combat = next(row for row in index if row['slug'] == 'combat')
        for name in ('Heroic Dexterity', 'Backstab', 'Bow Mastery'):
            assert name in json.dumps(combat)
        retained = ART / 'wiki-source'
        if not retained.exists():
            shutil.copytree(checkout, retained, ignore=shutil.ignore_patterns('dist', '__pycache__'))
        for name in ('combat', 'features', 'recent-changes'):
            article = Path('wiki/articles') / (name + '.json')
            assert sha(retained / article) == sha(checkout / article)
    report = dict(release=RELEASE, predecessor=PREVIOUS, previous_manifest_sha256=sha(prev_manifest),
                  exact_predecessor_reproduced=True, files=len(after), retained=len(after)-len(changed),
                  changed=changed, package_sha256=sha(archive), manifest_sha256=sha(archive.with_suffix('.json')))
    save(HERE / 'candidate.json', report)
    print(report)

if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--articles-from', type=Path, default=ROOT / 'wiki')
    main(cli.parse_args().articles_from)
